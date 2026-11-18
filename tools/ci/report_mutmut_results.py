# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Final

_PACKAGE_THRESHOLDS: Final[dict[str, int]] = {
    "initbot-chat": 71,
    "initbot-core": 69,
    "initbot-web": 60,
}
_STATUS_FIELDS: Final[tuple[str, ...]] = (
    "killed",
    "survived",
    "no_tests",
    "skipped",
    "suspicious",
    "timeout",
    "check_was_interrupted_by_user",
    "segfault",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("results_dir", type=Path)
    args = parser.parse_args()

    report, errors = _create_report(
        args.results_dir,
        os.environ.get("MUTATION_TESTING_RESULT", "success"),
    )
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with Path(summary_path).open("a", encoding="utf-8") as summary_file:
            summary_file.write(f"{report}\n")
    else:
        print(report)

    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    return 1 if errors else 0


def _create_report(
    results_dir: Path, mutation_job_result: str
) -> tuple[str, list[str]]:
    rows = [
        "| Package | Score | Killed | Survived | No tests | Skipped | Timeouts | Gate |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    errors: list[str] = []
    totals = dict.fromkeys(_STATUS_FIELDS, 0)

    if mutation_job_result != "success":
        errors.append(f"Mutation matrix finished with result: {mutation_job_result}")

    for package, threshold in _PACKAGE_THRESHOLDS.items():
        row, stats, package_errors = _package_summary(results_dir, package, threshold)
        rows.append(row)
        errors.extend(package_errors)
        if stats is not None:
            for field in _STATUS_FIELDS:
                totals[field] += stats[field]

    total_mutants = sum(totals.values())
    eligible_mutants = total_mutants - totals["no_tests"] - totals["skipped"]
    if eligible_mutants:
        overall_score = 100 * totals["killed"] / eligible_mutants
        rows.append(
            f"| **Overall** | **{overall_score:.1f}%** | **{totals['killed']}** | "
            f"**{totals['survived']}** | **{totals['no_tests']}** | "
            f"**{totals['skipped']}** | **{totals['timeout']}** | — |"
        )
    else:
        rows.append("| **Overall** | n/a | 0 | 0 | 0 | 0 | 0 | FAIL |")
        errors.append("No eligible mutants were reported")

    report = "\n".join([
        "## Mutation testing summary",
        "",
        "Score = killed / eligible mutants; no-test and skipped mutants are excluded. "
        "Timeouts and other non-killed outcomes count against the score.",
        "",
        *rows,
    ])
    return report, errors


def _package_summary(
    results_dir: Path, package: str, threshold: int
) -> tuple[str, dict[str, int] | None, list[str]]:
    stats_path = results_dir / f"mutation-results-{package}" / "mutmut-cicd-stats.json"
    try:
        stats = _read_stats(stats_path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return (
            f"| {package} | n/a | n/a | n/a | n/a | n/a | n/a | FAIL |",
            None,
            [f"{package}: could not read valid mutation stats ({error})"],
        )

    denominator = stats["total"] - stats["no_tests"] - stats["skipped"]
    score = 100 * stats["killed"] / denominator
    passed = stats["killed"] * 100 >= threshold * denominator
    errors = (
        []
        if passed
        else [f"{package}: mutation score {score:.1f}% is below {threshold}%"]
    )
    row = (
        f"| {package} | {score:.1f}% | {stats['killed']} | {stats['survived']} | "
        f"{stats['no_tests']} | {stats['skipped']} | {stats['timeout']} | "
        f"{'PASS' if passed else 'FAIL'} ({threshold}%) |"
    )
    return row, stats, errors


def _read_stats(stats_path: Path) -> dict[str, int]:
    with stats_path.open(encoding="utf-8") as stats_file:
        data = json.load(stats_file)
    if not isinstance(data, dict):
        raise ValueError("stats must be a JSON object")

    stats: dict[str, int] = {}
    for field in (*_STATUS_FIELDS, "total"):
        value = data.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"{field} must be a non-negative integer")
        stats[field] = value

    if stats["total"] == 0:
        raise ValueError("total must be greater than zero")
    if sum(stats[field] for field in _STATUS_FIELDS) != stats["total"]:
        raise ValueError("status counts do not add up to total")
    if stats["total"] - stats["no_tests"] - stats["skipped"] <= 0:
        raise ValueError("there are no eligible mutants")
    return stats


if __name__ == "__main__":
    raise SystemExit(main())
