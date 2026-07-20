# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import subprocess
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Final

_PACKAGE_ROOT = Path(__file__).resolve().parents[1]
_SPEC = spec_from_file_location(
    "auto_remediate",
    _PACKAGE_ROOT / "tools" / "auto_remediate.py",
)
_UV_AUDIT_NO_VULN: Final[str] = '{"summary":{"vulnerabilities":0,"adverse_statuses":0}}'
_UV_AUDIT_ONE_VULN: Final[str] = (
    '{"summary":{"vulnerabilities":1,"adverse_statuses":0}, "vulnerabilities":[ { "dependency": { "name": "click", "version": "8.3.2" }, "id": "PYSEC-2026-2132", "display_id": "PYSEC-2026-2132", "aliases": [ "CVE-2026-7246", "GHSA-47fr-3ffg-hgmw" ], "summary": null, "description": "Pallets Click, versions 8.3.2 and below, contain a command injection vulnerability in the click.edit() function, allowing attackers to pass arbitrary OS commands from an unprivileged account.", "link": "https://access.redhat.com/errata/RHSA-2026:24761", "fix_versions": [ "8.3.3" ], "published": "2026-04-30T14:16:36.433Z", "modified": "2026-07-13T07:15:21.899333658Z" } ]}'
)
auto_remediate = module_from_spec(_SPEC)
sys.modules["auto_remediate"] = auto_remediate
assert _SPEC.loader is not None
_SPEC.loader.exec_module(auto_remediate)


def test_create_validation_environment_uses_ephemeral_venv(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        auto_remediate.tempfile,
        "mkdtemp",
        lambda prefix="", dir=None: str(tmp_path / "remediator-venv"),
    )

    calls: list[str] = []

    def fake_run_cmd(
        cmd: str, *, check: bool = True, env: dict[str, str] | None = None
    ):  # pylint: disable=unused-argument
        calls.append(cmd)
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(auto_remediate, "_run_cmd", fake_run_cmd)

    validation_env = auto_remediate._create_validation_environment()  # pylint: disable=protected-access

    assert calls[0].startswith("uv venv ")
    assert validation_env["UV_PROJECT_ENVIRONMENT"] == str(tmp_path / "remediator-venv")
    assert validation_env["VIRTUAL_ENV"] == str(tmp_path / "remediator-venv")


def test_persist_internal_lockfile_copies_updated_lockfile(
    tmp_path: Path, monkeypatch
) -> None:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    host_lockfile = repo_dir / "uv.lock"
    host_lockfile.write_text("host-lock\n")

    monkeypatch.chdir(repo_dir)

    auto_remediate._ROOT = repo_dir  # pylint: disable=protected-access
    auto_remediate._INTERNAL_LOCK_FILE = repo_dir / "uv.lock"  # pylint: disable=protected-access
    auto_remediate._EXTERNAL_LOCK_FILE = repo_dir / "uv.lock-auto-remediated"  # pylint: disable=protected-access

    auto_remediate._externalise_lock_file()  # pylint: disable=protected-access

    assert (repo_dir / "uv.lock-auto-remediated").read_text() == "host-lock\n"


def test_main_defaults_to_single_run_without_sleeping(monkeypatch) -> None:
    def fake_run_cmd(
        cmd: str, *, check: bool = True, env: dict[str, str] | None = None
    ):  # pylint: disable=unused-argument
        return subprocess.CompletedProcess(
            args=cmd, returncode=0, stdout=_UV_AUDIT_NO_VULN, stderr=""
        )

    monkeypatch.setattr(auto_remediate, "_run_cmd", fake_run_cmd)
    monkeypatch.setattr(
        auto_remediate.time,
        "sleep",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("sleep should not be called")
        ),
    )

    exit_code = auto_remediate._main([])  # pylint: disable=protected-access

    assert exit_code == 0


def test_main_loop_mode_keeps_retrying_until_success(monkeypatch) -> None:
    call_count = {"value": 0}

    def fake_run_cmd(
        cmd: str, *, check: bool = True, env: dict[str, str] | None = None
    ):  # pylint: disable=unused-argument
        call_count["value"] += 1

        if call_count["value"] > 6:
            print(
                "Fatal escape hatch; too many calls to _run_cmd in test_main_loop_mode_keeps_retrying_until_success"
            )
            sys.exit(1)

        if cmd.startswith("uv audit"):
            if call_count["value"] == 1:
                return subprocess.CompletedProcess(
                    args=cmd, returncode=0, stdout=_UV_AUDIT_NO_VULN, stderr=""
                )
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=1,
                stdout=_UV_AUDIT_ONE_VULN,
                stderr="",
            )
        if (
            cmd.startswith("uv lock")
            or cmd.startswith("uv sync")
            or cmd.startswith("uv run")
            or cmd.startswith("uv venv")
        ):
            return subprocess.CompletedProcess(
                args=cmd, returncode=0, stdout="", stderr=""
            )
        raise ValueError(f"Unexpected command: {cmd}")

    monkeypatch.setattr(auto_remediate, "_run_cmd", fake_run_cmd)

    sleep_calls: list[int] = []

    def fake_sleep(seconds: int) -> None:
        sleep_calls.append(seconds)

    monkeypatch.setattr(auto_remediate.time, "sleep", fake_sleep)

    # pylint: disable=protected-access
    exit_code = auto_remediate._main([
        "--loop-until-update",
        "--sleep-seconds",
        "1",
    ])

    assert exit_code == 1
    assert sleep_calls == [1]
