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


@dataclasses.dataclass
class VulnerabilityState:
    has_vulnerabilities: bool = False


def _get_vulnerabilities_sync() -> list[tuple[str, str, str]]:
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
    return [
        (name, version, vuln["id"])
        for (name, version), result in zip(
            installed, results.get("results", []), strict=False
        )
        for vuln in result.get("vulns", [])
    ]


async def get_vulnerabilities() -> list[tuple[str, str, str]]:
    """Return (name, version, vuln_id) for every vulnerability found in installed packages.

    Logs errors at DEBUG level on failure. Never raises.
    """
    try:
        return await asyncio.get_event_loop().run_in_executor(
            None, _get_vulnerabilities_sync
        )
    except URLError as exc:
        _log.debug("Vulnerability check skipped (network error): %s", exc)
    except Exception as exc:  # pylint: disable=broad-except  # noqa: BLE001
        _log.debug("Vulnerability check failed: %s", exc)
    return []


async def check_vulnerabilities() -> None:
    """Query the OSV database for known vulnerabilities in the installed packages.

    Logs a warning for each vulnerability found. Never raises — network errors
    and other failures are logged at DEBUG level so startup is never blocked.
    """
    for name, version, vuln_id in await get_vulnerabilities():
        _log.warning("Security vulnerability in %s %s: %s", name, version, vuln_id)
