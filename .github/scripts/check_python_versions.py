# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

#!/usr/bin/env python3
"""Check that the project's supported Python versions are current."""

import json
import re
import sys
import tomllib
import urllib.request
from collections.abc import Collection, Mapping, Set
from datetime import date
from pathlib import Path
from typing import Any, Final


def main() -> None:
    supported = _get_python_versions_supported_by_project()

    url = "https://endoflife.date/api/python.json"
    with urllib.request.urlopen(url) as resp:
        data = json.loads(resp.read())
        if not isinstance(data, Collection):
            raise ValueError(
                f"https://endoflife.date/api/python.json returned unparseable data ({type(data)}, {data})"
            )
        python_releases: Collection[Mapping[str, Any]] = data

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

    project_file_path: Final[Path] = Path("./packages/initbot-web/pyproject.toml")
    with project_file_path.open("rb") as file_obj:
        pyproject_toml_dict = tomllib.load(file_obj)

    for classifier in pyproject_toml_dict.get("project", {}).get("classifiers", []):
        nouns: Final[Collection[str]] = tuple(
            part.strip() for part in classifier.split("::")
        )
        if (
            len(nouns) == 3
            and nouns[0] == "Programming Language"
            and nouns[1] == "Python"
        ):
            if not re.fullmatch(r"3\.[0-9]+", nouns[2]):
                raise ValueError(
                    f"The Python version specifier {nouns[2]} in {project_file_path} does not have the expected minor-version format"
                )
            supported.add(nouns[2])

    if len(supported) < 4:
        raise ValueError(
            "The project configuration is expected to support all released Python versions that aren't at end of life. However, .python-version seems to specify less than four which seems too few."
        )

    return supported


def _get_end_of_life_issues(
    supported: Set[str], python_releases: Collection[Mapping[str, Any]]
) -> Collection[str]:
    today: Final[date] = date.today()
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
    supported: Set[str], python_releases: Collection[Mapping[str, Any]]
) -> Collection[str]:
    today: Final[date] = date.today()
    issues = list[str]()
    max_supported: Final[str] = max(
        supported, key=lambda v: tuple(int(x) for x in v.split("."))
    )
    max_minor: Final[tuple[int, ...]] = tuple(int(x) for x in max_supported.split("."))

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
