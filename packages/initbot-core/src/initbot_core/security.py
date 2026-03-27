# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import asyncio
import dataclasses
import importlib.metadata
import json
import logging
import urllib.request
from urllib.error import URLError

_log = logging.getLogger(__name__)

_OSV_QUERYBATCH_URL = "https://api.osv.dev/v1/querybatch"
_OSV_VULN_URL = "https://api.osv.dev/v1/vulns/{}"
_HIGH_SEVERITIES: frozenset[str] = frozenset({"HIGH", "CRITICAL"})


@dataclasses.dataclass
class VulnerabilityState:
    has_high_severity_vulnerabilities: bool = False


def _fetch_severity(vuln_id: str) -> str:
    """Return the database_specific severity string for a single OSV vulnerability."""
    req = urllib.request.Request(_OSV_VULN_URL.format(vuln_id))  # noqa: S310
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
            data = json.loads(resp.read())
        return str(data.get("database_specific", {}).get("severity", ""))
    except Exception:  # pylint: disable=broad-except
        return ""


def _get_vulnerabilities_sync() -> list[tuple[str, str, str, str]]:
    installed = [
        (dist.metadata["Name"], dist.version)
        for dist in importlib.metadata.distributions()
        if dist.metadata["Name"]
    ]
    queries = [
        {"package": {"ecosystem": "PyPI", "name": name}, "version": version}
        for name, version in installed
    ]
    payload = json.dumps({"queries": queries}).encode()
    req = urllib.request.Request(  # noqa: S310
        _OSV_QUERYBATCH_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
        results = json.loads(resp.read())
    found = [
        (name, version, vuln["id"])
        for (name, version), result in zip(
            installed, results.get("results", []), strict=False
        )
        for vuln in result.get("vulns", [])
    ]
    return [
        (name, version, vuln_id, _fetch_severity(vuln_id))
        for name, version, vuln_id in found
    ]


async def get_vulnerabilities() -> list[tuple[str, str, str, str]]:
    """Return (name, version, vuln_id, severity) for every vulnerability found in installed packages.

    Logs errors at DEBUG level on failure. Never raises.
    """
    try:
        return await asyncio.get_event_loop().run_in_executor(
            None, _get_vulnerabilities_sync
        )
    except URLError as exc:
        _log.debug("Vulnerability check skipped (network error): %s", exc)
    except Exception as exc:  # pylint: disable=broad-except
        _log.debug("Vulnerability check failed: %s", exc)
    return []


def is_high_severity(severity: str) -> bool:
    """Return True if severity is HIGH or CRITICAL."""
    return severity in _HIGH_SEVERITIES
