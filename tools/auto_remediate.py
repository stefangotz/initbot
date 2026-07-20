#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Automatically remediate known Python dependency vulnerabilities on a host."""

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
# The "normal" uv.lock file copied from the host into the container at build time.
_INTERNAL_LOCK_FILE: Final[Path] = _ROOT / "uv.lock"
# A pre-arranged path that is mapped to the host system (see compose.yml).
_EXTERNAL_LOCK_FILE: Final[Path] = _ROOT / "uv.lock-auto-remediated"


@dataclass(frozen=True)
class Vuln:
    name: str
    version: Version
    fix_versions: tuple[Version]


def _main(argv: list[str] | None = None) -> int:
    """Remediate dependency vulnerabilities (if any) either as a one-shot attempt (mainly for debugging) or in a loop until remediation is in fact required (standard behaviour in remediation container).

    The overall contract between this application and its runtime (compose stack and run.sh) is:
    - run continuously until dependencies have been successfully updated to address vulnerabilities
    - when dependencies have been updated:
        - write updated lock file to _EXTERNAL_LOCK_FILE
        - exit with a non-zero exit code
    Based on this contract, the runtime will rebuild and restart the application stack.
    """
    args = _parse_args(argv)

    if not args.loop_until_update:
        _check_and_remediate(args.test_command)
        return 0

    while True:
        try:
            remediated = _check_and_remediate(args.test_command)
        except Exception as exc:
            print(f"Unexpected error occurred: {exc}", file=sys.stderr)
            # Approach is to keep trying instead of exiting on failures.
            # Pro: avoids spurious, unjustified application restarts
            # Con: may prevent necessary remediation and mask persistent issues that require intervention
            remediated = False

        if remediated:
            return 1

        time.sleep(args.sleep_seconds)


def _check_and_remediate(test_command: str) -> bool:
    """Check for known vulnerabilities in dependencies. If found, update them and run tests for validation.

    Returns True if remediation was performed, False otherwise.
    """
    print("--- Starting automatic dependency remediation ---")

    audit_cmd: Final[str] = (
        "uv audit --no-dev --preview-features audit,json-output --color never --no-progress --output-format json --quiet"
    )
    audit_result = _run_cmd(
        audit_cmd,
        check=False,
    )
    if audit_result.returncode > 1:
        raise RuntimeError(
            f"'{audit_cmd} failed with exit code {audit_result.returncode}: {audit_result.stderr}"
        )

    report = json.loads(audit_result.stdout)

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

    return _remediate(vulns, test_command)


def _remediate(vulns: Set[Vuln], test_command: str) -> bool:
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

    _externalise_lock_file()

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
        name: Final[str] = vulnerability["dependency"]["name"]
        version: Final[str] = vulnerability["dependency"]["version"]
        fix_versions: Final[tuple[str]] = tuple(vulnerability["fix_versions"])
        result.add(Vuln(name=name, version=version, fix_versions=fix_versions))

    return result


def _create_validation_environment() -> dict[str, str]:
    """Create a dedicated ephemeral virtual environment for validation inside the container."""
    venv_dir = Path(tempfile.mkdtemp(prefix="auto-remediate-", dir="/tmp"))
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


def _externalise_lock_file() -> None:
    """Copy the updated lockfile to a path from which it can be promoted."""
    if _INTERNAL_LOCK_FILE.exists():
        shutil.copy2(_INTERNAL_LOCK_FILE, _EXTERNAL_LOCK_FILE)


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
    return parser.parse_args(argv)


def _get_least_version_greater_than(
    versions: Iterable[Version], base_version: Version
) -> Version:
    """Return the least version from the given list that is greater than the base version."""
    return min(v for v in versions if v > base_version)


if __name__ == "__main__":
    sys.exit(_main())
