# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
from pathlib import Path

from tools.report_mutmut_results import _create_report


def _write_stats(results_dir: Path, package: str, stats: dict[str, int]) -> None:
    artifact_dir = results_dir / f"mutation-results-{package}"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    (artifact_dir / "mutmut-cicd-stats.json").write_text(json.dumps(stats))


def _stats(
    *,
    killed: int,
    survived: int,
    no_tests: int = 0,
    skipped: int = 0,
    timeout: int = 0,
) -> dict[str, int]:
    return {
        "killed": killed,
        "survived": survived,
        "no_tests": no_tests,
        "skipped": skipped,
        "suspicious": 0,
        "timeout": timeout,
        "check_was_interrupted_by_user": 0,
        "segfault": 0,
        "total": killed + survived + no_tests + skipped + timeout,
    }


def test_score_gate_excludes_no_tests_and_skipped_but_counts_timeouts(
    tmp_path: Path,
) -> None:
    _write_stats(
        tmp_path,
        "initbot-chat",
        _stats(killed=65, survived=25, no_tests=5, skipped=4, timeout=1),
    )
    _write_stats(tmp_path, "initbot-core", _stats(killed=69, survived=31))
    _write_stats(tmp_path, "initbot-web", _stats(killed=60, survived=40))

    report, errors = _create_report(tmp_path, "success")

    assert not errors
    assert "| initbot-chat | 71.4% | 65 | 25 | 5 | 4 | 1 | PASS (71%) |" in report
    assert "| **Overall** | **66.7%** |" in report


def test_score_gate_fails_when_package_is_below_its_floor(tmp_path: Path) -> None:
    _write_stats(tmp_path, "initbot-chat", _stats(killed=146, survived=58))
    _write_stats(tmp_path, "initbot-core", _stats(killed=68, survived=32))
    _write_stats(tmp_path, "initbot-web", _stats(killed=488, survived=315))

    report, errors = _create_report(tmp_path, "success")

    assert "| initbot-core | 68.0% | 68 | 32 | 0 | 0 | 0 | FAIL (69%) |" in report
    assert errors == ["initbot-core: mutation score 68.0% is below 69%"]


def test_report_fails_when_matrix_failed_or_stats_are_missing(tmp_path: Path) -> None:
    _write_stats(tmp_path, "initbot-chat", _stats(killed=146, survived=58))

    report, errors = _create_report(tmp_path, "failure")

    assert "Mutation matrix finished with result: failure" in errors
    assert any(
        "initbot-core: could not read valid mutation stats" in error for error in errors
    )
    assert "| initbot-web | n/a |" in report
