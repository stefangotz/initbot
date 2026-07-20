# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
import subprocess
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SPEC = spec_from_file_location(
    "auto_remediate",
    PACKAGE_ROOT / "tools" / "auto_remediate.py",
)
auto_remediate = module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(auto_remediate)


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


def test_extract_vulnerable_packages_from_packages_list() -> None:
    payload = {
        "packages": [
            {"name": "requests", "version": "2.31.0"},
            {"name": "urllib3", "version": "2.2.0"},
        ]
    }

    # pylint: disable=protected-access
    assert auto_remediate._extract_vulnerable_packages(payload) == {
        "requests",
        "urllib3",
    }  # pylint: disable=protected-access


def test_extract_vulnerable_packages_from_dependency_entries() -> None:
    payload = {
        "dependencies": [
            {"name": "jinja2", "version": "3.1.0"},
            {"name": "pydantic", "version": "2.0.0"},
        ]
    }

    # pylint: disable=protected-access
    assert auto_remediate._extract_vulnerable_packages(payload) == {
        "jinja2",
        "pydantic",
    }  # pylint: disable=protected-access


def test_main_defaults_to_single_run_without_sleeping(monkeypatch) -> None:
    def fake_run_cmd(
        cmd: str, *, check: bool = True, env: dict[str, str] | None = None
    ):  # pylint: disable=unused-argument
        return subprocess.CompletedProcess(
            args=cmd, returncode=0, stdout="{}", stderr=""
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
        if call_count["value"] == 1:
            return subprocess.CompletedProcess(
                args=cmd, returncode=0, stdout="{}", stderr=""
            )
        if cmd.startswith("uv audit"):
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=1,
                stdout=json.dumps({"packages": [{"name": "requests"}]}),
                stderr="",
            )
        if cmd.startswith("uv lock"):
            return subprocess.CompletedProcess(
                args=cmd, returncode=0, stdout="", stderr=""
            )
        if cmd.startswith("uv sync"):
            return subprocess.CompletedProcess(
                args=cmd, returncode=0, stdout="", stderr=""
            )
        if cmd.startswith("uv run"):
            return subprocess.CompletedProcess(
                args=cmd, returncode=0, stdout="", stderr=""
            )
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

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


def test_main_loop_mode_keeps_retrying_until_restart_is_requested(monkeypatch) -> None:
    call_count = {"value": 0}

    def fake_run_cmd(
        cmd: str, *, check: bool = True, env: dict[str, str] | None = None
    ):  # pylint: disable=unused-argument
        call_count["value"] += 1
        if call_count["value"] == 1:
            return subprocess.CompletedProcess(
                args=cmd, returncode=0, stdout="{}", stderr=""
            )
        if cmd.startswith("uv audit"):
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=1,
                stdout=json.dumps({"packages": [{"name": "requests"}]}),
                stderr="",
            )
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

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
