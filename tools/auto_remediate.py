#!/usr/bin/env -S uv run --script
# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# /// script
# requires-python = ">=3.11"
# dependencies = ["packaging @ https://files.pythonhosted.org/packages/63/34/ba1c580383c9eada3711951fef0795c80b829a078d72188184bcab9dd527/packaging-26.3-py3-none-any.whl#sha256=d7193f7c8e4e93f444fde0262bf90af30e16fa0ad0ad44cb553c87339b23cd1c"]
# ///

"""Automatically remediate known Python dependency vulnerabilities in a uv lock file."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Iterable, Set
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from packaging.version import Version

_ROOT: Final[Path] = Path.cwd()
_PROJECT_LOCK_FILE: Final[Path] = Path.cwd() / "uv.lock"


@dataclass(frozen=True)
class Vuln:
    name: str
    version: Version
    fix_versions: tuple[Version, ...]


def _main(argv: list[str] | None = None) -> int:
    """Remediate dependency vulnerabilities (if any) either as a one-shot attempt (mainly for debugging) or in a loop until remediation is in fact required (standard behaviour in remediation container).

    Can be invoked from the project repository with the default arguments to check and remediate vulnerabilities once.

    The main intended use case however is for this application to run inside a sidecar container to perform remediation for some other containerised application.
    In that scenario, the overall contract between this application and its containerised runtime (compose stack and run.sh) is:
    - copy the input uv.lock file to the project directory as `uv.lock` for uv to operate on
    - run continuously until dependencies have been successfully updated to address vulnerabilities
    - when dependencies have been updated:
        - copy updated project uv.lock to output path
        - exit with a non-zero exit code
    Based on this contract, the runtime will copy the output path to the host system's "real" uv.lock file, rebuild the stack (which updates the Python dependencies as per the lock file), and restart the application stack.
    """
    args = _parse_args(argv)

    if not args.loop_until_update:
        _check_and_remediate(
            args.input_lock_file, args.test_command, args.output_lock_file
        )
        return 0

    while True:
        try:
            remediated = _check_and_remediate(
                args.input_lock_file, args.test_command, args.output_lock_file
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            print(f"Unexpected error occurred: {exc}", file=sys.stderr)
            # Approach is to keep trying instead of exiting on failures.
            # Pro: avoids spurious, unjustified application restarts
            # Con: may prevent necessary remediation and mask persistent issues that require intervention
            remediated = False

        if remediated:
            return 1

        time.sleep(args.sleep_seconds)


def _write_project_lock_file(input_lock_file: Path) -> None:
    """Set up the project uv.lock file for uv to operate on by copying it from the input lock file path."""
    if not _PROJECT_LOCK_FILE.exists() or not input_lock_file.samefile(
        _PROJECT_LOCK_FILE
    ):
        shutil.copy2(input_lock_file, _PROJECT_LOCK_FILE)


def _check_and_remediate(
    input_lock_file: Path, test_command: str, output_lock_file: Path
) -> bool:
    """Check for known vulnerabilities in dependencies. If found, update them and run tests for validation.

    Returns True if remediation was performed, False otherwise.
    """
    print("--- Starting automatic dependency remediation ---")

    _write_project_lock_file(input_lock_file)

    audit_cmd: Final[str] = (
        "uv audit --no-dev --preview-features audit,json-output --color never --no-progress --output-format json --quiet --frozen"
    )
    audit_result = _run_cmd(
        audit_cmd,
        check=False,
    )
    if audit_result.returncode > 1:
        raise RuntimeError(
            f"'{audit_cmd} failed with exit code {audit_result.returncode}: {audit_result.stderr}"
        )

    try:
        report = json.loads(audit_result.stdout)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"'{audit_cmd}' returned invalid JSON: {audit_result.stdout!r}"
        ) from e

    if audit_result.returncode == 0:
        if (
            report["summary"]["vulnerabilities"] == 0
            and report["summary"]["adverse_statuses"] == 0
        ):
            print("No vulnerabilities detected; nothing to do.")
            return False

        raise ValueError(
            f"'{audit_cmd}' returned with exit code 0, but its output ({report}) unexpectedly does not seem to indicate an absence of vulnerabilities."
        )

    vulns = _extract_vulnerabilities(report)

    if not vulns:
        raise ValueError(
            f"'{audit_cmd}' reported vulnerabilities, but no vulnerability information could be parsed from its output ({report})."
        )

    return _remediate(vulns, test_command, output_lock_file)


def _remediate(vulns: Set[Vuln], test_command: str, output_lock_file: Path) -> bool:
    """Attempt to remediate the given vulnerabilities by upgrading the affected packages and running tests for validation."""
    print(f"Detected vulnerabilities: {vulns}")

    validation_env = _create_validation_environment()
    try:
        cmd = "uv lock"
        for vuln in vulns:
            fix_version = _get_least_version_greater_than(
                vuln.fix_versions, vuln.version
            )
            print(f"Upgrading package {vuln.name} from {vuln.version} to {fix_version}")
            cmd += f" --upgrade-package {vuln.name}=={fix_version}"

        print("Updating lock file")
        _run_cmd(cmd, env=validation_env)

        print("Syncing venv")
        _run_cmd("uv sync", env=validation_env)

        print("Running validation suite against updated venv")
        _run_cmd(test_command, check=True, env=validation_env)
    finally:
        _cleanup_validation_environment(validation_env)

    _write_output_lock_file(output_lock_file)

    print("--- Automatic remediation completed successfully ---")
    return True


def _run_cmd(
    cmd: str, *, check: bool = True, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """Run a shell command and return the completed process."""
    argv = shlex.split(cmd)
    result = subprocess.run(  # noqa: S603
        argv,
        capture_output=True,
        text=True,
        cwd=_ROOT,
        env=env,
        check=False,
    )

    if check and result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Command failed ({result.returncode}): {cmd}\n{stderr}")

    return result


def _extract_vulnerabilities(payload: dict[str, Any]) -> set[Vuln]:
    result = set[Vuln]()

    for vulnerability in payload.get("vulnerabilities", []):
        result.add(
            Vuln(
                vulnerability["dependency"]["name"],
                Version(vulnerability["dependency"]["version"]),
                tuple(Version(v) for v in vulnerability["fix_versions"]),
            )
        )

    return result


def _create_validation_environment() -> dict[str, str]:
    """Create a dedicated ephemeral virtual environment for validation inside the container."""
    venv_dir = Path(tempfile.mkdtemp(prefix="auto-remediate-"))
    env = os.environ.copy()
    env["UV_PROJECT_ENVIRONMENT"] = str(venv_dir)
    env["VIRTUAL_ENV"] = str(venv_dir)
    _run_cmd(f"uv venv {shlex.quote(str(venv_dir))}", env=env)
    return env


def _cleanup_validation_environment(env: dict[str, str]) -> None:
    """Remove the temporary validation environment once validation is complete."""
    venv_path = env.get("VIRTUAL_ENV")
    if venv_path:
        shutil.rmtree(venv_path, ignore_errors=True)


def _write_output_lock_file(output_lock_file: Path) -> None:
    """Write the updated lockfile to the output path (from where the caller of this script can promote it."""
    if not output_lock_file.exists() or not _PROJECT_LOCK_FILE.samefile(
        output_lock_file
    ):
        shutil.copy2(_PROJECT_LOCK_FILE, output_lock_file)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--test-command",
        default="uv run pytest --ignore=tests/test_auto_remediate.py --ignore=tests/layout",
        help="Command to run for validation before deployment",
    )
    parser.add_argument(
        "--loop-until-update",
        action="store_true",
        help="Keep running until a restart request is generated after a dependency update",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=int,
        default=60,
        help="Delay between remediation attempts when --loop-until-update is enabled",
    )
    parser.add_argument(
        "--input-lock-file",
        "-i",
        type=Path,
        default=Path.cwd() / "uv.lock",
        help="The path of the input uv.lock file to check and update",
    )
    parser.add_argument(
        "--output-lock-file",
        "-o",
        type=Path,
        default=Path.cwd() / "uv.lock",
        help="The path where to write the updated output uv.lock file",
    )
    return parser.parse_args(argv)


def _get_least_version_greater_than(
    versions: Iterable[Version], base_version: Version
) -> Version:
    """Return the least version from the given list that is greater than the base version."""
    return min(v for v in versions if v > base_version)


if __name__ == "__main__":
    sys.exit(_main())
