# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

#!/usr/bin/env python3
"""Check that the project's supported Python versions are current."""

import json
import sys
import urllib.request
from collections.abc import Collection, Mapping, Set
from datetime import date
from pathlib import Path
from typing import Any


def main() -> None:
    supported = _get_python_versions_supported_by_project()

    url = "https://endoflife.date/api/python.json"
    with urllib.request.urlopen(url) as resp:
        data = json.loads(resp.read())
        if not isinstance(data, dict):
            raise ValueError(
                "https://endoflife.date/api/python.json returned unparseable data"
            )
        python_releases: dict[str, Any] = data

    issues: list[str] = []

    issues.extend(_get_end_of_life_issues(supported, python_releases))
    issues.extend(_get_new_releases_issues(supported, python_releases))

    if issues:
        print("Python version lifecycle issues detected:")
        for issue in issues:
            print(f"  - {issue}")
        sys.exit(1)

    print(f"Python version check passed. Supported: {sorted(supported)}")


def _get_python_versions_supported_by_project() -> Set[str]:
    supported = set()
    for line in Path(".python-version").read_text(encoding="UTF8").splitlines():
        line = line.strip()
        if line:
            parts = line.split(".")
            supported.add(f"{parts[0]}.{parts[1]}")

    if len(supported) < 4:
        raise ValueError(
            "The project configuration is expected to support all released Python versions that aren't at end of life. However, .python-version seems to specify less than four which seems too few."
        )

    return supported


def _get_end_of_life_issues(
    supported: Set[str], python_releases: Mapping[str, Any]
) -> Collection[str]:
    today = date.today()
    issues = list[str]()
    for entry in python_releases:
        cycle: str = entry["cycle"]
        if cycle not in supported:
            continue
        eol = entry["eol"]
        if eol is False:
            continue
        if date.fromisoformat(eol) <= today:
            issues.append(
                f"Python {cycle} reached end of life on {eol}"
                " — remove from .python-version and CI matrix"
            )

    return issues


def _get_new_releases_issues(
    supported: Set[str], python_releases: Mapping[str, Any]
) -> Collection[str]:
    today = date.today()
    issues = list[str]()
    max_supported = max(supported, key=lambda v: tuple(int(x) for x in v.split(".")))
    max_minor = tuple(int(x) for x in max_supported.split("."))

    for entry in python_releases:
        cycle = entry["cycle"]
        if cycle in supported:
            continue
        release_date_str: str | None = entry.get("releaseDate")
        if not release_date_str:
            continue
        if date.fromisoformat(release_date_str) > today:
            continue
        try:
            cycle_version = tuple(int(x) for x in cycle.split("."))
        except ValueError:
            continue
        if cycle_version > max_minor:
            issues.append(
                f"Python {cycle} was released on {release_date_str}"
                " — add to .python-version and CI matrix"
            )

    return issues


if __name__ == "__main__":
    main()
