# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
from asyncio import CancelledError, create_task, sleep
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress
from pathlib import Path

import uvicorn
from starlette.applications import Starlette
from starlette.templating import Jinja2Templates
from starlette.types import ASGIApp

from initbot_core.security import (
    VulnerabilityState,
    get_vulnerabilities,
    is_high_severity,
)
from initbot_core.state.factory import create_state_from_source
from initbot_web.config import WebSettings
from initbot_web.routes.tracker import make_routes

_log = logging.getLogger(__name__)


async def _periodic_vulnerability_check(vuln_state: VulnerabilityState) -> None:
    while True:
        vulns = await get_vulnerabilities()
        for name, version, vuln_id, severity in vulns:
            _log.warning(
                "Security vulnerability in %s %s: %s (severity: %s)",
                name,
                version,
                vuln_id,
                severity or "unknown",
            )
        vuln_state.has_high_severity_vulnerabilities = any(
            is_high_severity(severity) for _, _, _, severity in vulns
        )
        await sleep(24 * 60 * 60)


def create_app(settings: WebSettings | None = None) -> Starlette:
    cfg = settings or WebSettings()
    if not cfg.state.startswith("sqlite:"):
        raise SystemExit(f"initbot-web requires a SQLite state URI. Got: {cfg.state!r}")
    state = create_state_from_source(cfg.state)
    templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
    vuln_state = VulnerabilityState()

    @asynccontextmanager
    async def lifespan(_app: ASGIApp) -> AsyncGenerator[None, None]:
        task = create_task(_periodic_vulnerability_check(vuln_state))
        yield
        task.cancel()
        with suppress(CancelledError):
            await task

    return Starlette(
        routes=make_routes(state, templates, cfg.web_secret, vuln_state),
        lifespan=lifespan,
    )


def run() -> None:
    cfg = WebSettings(_cli_parse_args=True)  # type: ignore
    print(f"URL: http://localhost:{cfg.web_port}/s/{cfg.web_secret}/")
    uvicorn.run(create_app(cfg), host=cfg.web_host, port=cfg.web_port)
