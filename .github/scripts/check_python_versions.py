# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

#!/usr/bin/env python3
"""Check that the project's supported Python versions are current."""

import json
import sys
import urllib.request
from datetime import date
from pathlib import Path


def main() -> None:
    today = date.today()

    supported = set()
    for line in Path(".python-version").read_text().splitlines():
        line = line.strip()
        if line:
            parts = line.split(".")
            supported.add(f"{parts[0]}.{parts[1]}")

    url = "https://endoflife.date/api/python.json"
    with urllib.request.urlopen(url) as resp:  # noqa: S310
        data = json.loads(resp.read())

    issues: list[str] = []

    for entry in data:
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

    max_supported = max(supported, key=lambda v: tuple(int(x) for x in v.split(".")))
    max_minor = tuple(int(x) for x in max_supported.split("."))

    for entry in data:
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

    if issues:
        print("Python version lifecycle issues detected:")
        for issue in issues:
            print(f"  - {issue}")
        sys.exit(1)

    print(f"Python version check passed. Supported: {sorted(supported)}")


if __name__ == "__main__":
    main()
