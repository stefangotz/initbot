# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Sync workspace pyproject.toml dependency specifiers with uv.lock.

Dependabot updates uv.lock but not workspace-member pyproject.toml files (see
AGENTS.md for context). Run this script on the Dependabot branch to fix the
mismatch, then commit the result and run `uv lock` to regenerate the lockfile
from the corrected pyproject.toml files.

Usage:
    uv run tools/fix_workspace_deps.py [--dry-run]
"""

import re
import subprocess
import sys
from pathlib import Path

import tomllib

ROOT = Path.cwd()


def normalize_name(name: str) -> str:
    """Normalize a PEP 503 package name to lowercase with hyphens."""
    return re.sub(r"[-_.]+", "-", name).lower()


def read_lockfile_from_git() -> dict:
    """Read uv.lock from the git HEAD commit, bypassing any on-disk regeneration."""
    result = subprocess.run(
        ["git", "show", "HEAD:uv.lock"],  # noqa: S607
        capture_output=True,
        text=True,
        check=True,
        cwd=ROOT,
    )
    return tomllib.loads(result.stdout)


def lockfile_workspace_packages(lockfile: dict) -> list[dict]:
    return [
        pkg
        for pkg in lockfile.get("package", [])
        if isinstance(pkg.get("source"), dict) and "editable" in pkg["source"]
    ]


def lockfile_specifiers(pkg: dict) -> dict[str, str]:
    """Return {normalized_name: specifier} from the package's requires-dist in the lockfile."""
    return {
        normalize_name(entry["name"]): entry["specifier"]
        for entry in pkg.get("metadata", {}).get("requires-dist", [])
        if entry.get("specifier")
    }


def pyproject_dep_specifier(pyproject_path: Path, dep_name: str) -> str | None:
    """Return the current specifier for dep_name in pyproject.toml, or None if not listed."""
    data = tomllib.loads(pyproject_path.read_text())
    deps = data.get("project", {}).get("dependencies", [])
    norm = normalize_name(dep_name)
    for dep_str in deps:
        # dep_str is a PEP 508 string: "name[extras][specifier][; marker]"
        raw_name = re.split(r"[><=!~\s;\[]", dep_str, maxsplit=1)[0]
        if normalize_name(raw_name) != norm:
            continue
        m = re.match(r"[A-Za-z0-9_.[\]-]+((?:[><=!~].+?)?)(\s*;.*)?$", dep_str)
        return m.group(1) if m else ""
    return None


def update_dep_specifier(
    pyproject_path: Path, dep_name: str, new_specifier: str
) -> bool:
    """Rewrite dep_name's version specifier in pyproject.toml. Returns True if changed."""
    text = pyproject_path.read_text()
    # Match the dep inside a quoted string, ensuring we don't partially match longer names
    # (e.g. "pydantic" must not match inside "pydantic-settings").
    norm = normalize_name(dep_name)
    # normalize_name converts all [-_.] to -, so re.escape only escapes -.
    # Replace the escaped \- with a character class to match any PEP 503 separator.
    name_pat = re.escape(norm).replace(r"\-", r"[-_.]")
    pattern = re.compile(
        r'("' + name_pat + r")"  # group 1: opening quote + exact name
        r"(?![-_.a-zA-Z0-9])"  # negative lookahead: not a longer name
        r"((?:[><=!~][^\";\s\[,]+"  # group 2: current specifier
        r"(?:,\s*[><=!~][^\";\s\[,]+)*)?)",
        re.IGNORECASE,
    )
    new_text, n = pattern.subn(lambda m: m.group(1) + new_specifier, text)
    if n == 0 or new_text == text:
        return False
    pyproject_path.write_text(new_text)
    return True


def main(argv: list[str]) -> int:
    dry_run = "--dry-run" in argv
    lockfile = read_lockfile_from_git()
    any_mismatch = False

    for pkg in lockfile_workspace_packages(lockfile):
        pkg_name = pkg["name"]
        editable_path = pkg["source"]["editable"]
        pyproject_path = ROOT / editable_path / "pyproject.toml"

        if not pyproject_path.exists():
            print(
                f"warning: {pyproject_path} not found, skipping {pkg_name}",
                file=sys.stderr,
            )
            continue

        for dep_name, lock_spec in lockfile_specifiers(pkg).items():
            current_spec = pyproject_dep_specifier(pyproject_path, dep_name)
            if current_spec is None or current_spec == lock_spec:
                continue

            rel = pyproject_path.relative_to(ROOT)
            print(f"{rel}: {dep_name}: {current_spec!r} → {lock_spec!r}")
            any_mismatch = True

            if not dry_run and not update_dep_specifier(
                pyproject_path, dep_name, lock_spec
            ):
                print(
                    f"  warning: could not update {dep_name} in {rel}", file=sys.stderr
                )

    if not any_mismatch:
        print("All workspace pyproject.toml files are in sync with uv.lock.")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
