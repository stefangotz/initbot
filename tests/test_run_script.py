# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import shutil
import subprocess
import time
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def test_run_script_promotes_newer_internal_lockfile(tmp_path: Path) -> None:
    repo_dir = tmp_path / "repo"
    (repo_dir / "tools").mkdir(parents=True)
    shutil.copyfile(PACKAGE_ROOT / "tools" / "run.sh", repo_dir / "tools" / "run.sh")
    (repo_dir / "tools" / "run.sh").chmod(0o755)

    docker_bin_dir = repo_dir / "bin"
    docker_bin_dir.mkdir()
    docker_bin = docker_bin_dir / "docker"
    docker_bin.write_text('#!/bin/sh\nprintf \'%s\\n\' "$*" >> "$DOCKER_LOG"\nexit 0\n')
    docker_bin.chmod(0o755)

    internal_lock_path = repo_dir / "uv.lock-auto-remediated"
    internal_lock_path.write_text("internal-lock\n")
    host_lock_path = repo_dir / "uv.lock"
    host_lock_path.write_text("host-lock\n")
    os.utime(internal_lock_path, (time.time() + 10, time.time() + 10))

    env = os.environ.copy()
    env["PATH"] = f"{docker_bin_dir}:{env['PATH']}"
    env["DOCKER_LOG"] = str(repo_dir / "docker.log")

    result = subprocess.run(
        ["/bin/sh", "tools/run.sh"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert host_lock_path.read_text() == "internal-lock\n"


def test_run_script_rebuilds_before_start_and_clears_restart_request(
    tmp_path: Path,
) -> None:
    repo_dir = tmp_path / "repo"
    (repo_dir / "tools").mkdir(parents=True)
    shutil.copyfile(PACKAGE_ROOT / "tools" / "run.sh", repo_dir / "tools" / "run.sh")
    (repo_dir / "tools" / "run.sh").chmod(0o755)

    docker_bin_dir = repo_dir / "bin"
    docker_bin_dir.mkdir()
    docker_bin = docker_bin_dir / "docker"
    docker_bin.write_text('#!/bin/sh\nprintf \'%s\\n\' "$*" >> "$DOCKER_LOG"\nexit 0\n')
    docker_bin.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{docker_bin_dir}:{env['PATH']}"
    env["DOCKER_LOG"] = str(repo_dir / "docker.log")

    result = subprocess.run(
        ["/bin/sh", "tools/run.sh"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    assert result.returncode == 0, result.stderr

    docker_log = (repo_dir / "docker.log").read_text()
    assert "compose up --build" in docker_log
