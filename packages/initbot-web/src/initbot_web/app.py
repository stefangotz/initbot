# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
import secrets
from asyncio import CancelledError, create_task, sleep
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress
from pathlib import Path

import uvicorn
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.templating import Jinja2Templates
from starlette.types import ASGIApp

from initbot_core.config import CORE_CFG
from initbot_core.security import (
    VulnerabilityState,
    get_vulnerabilities,
    is_high_severity,
)
from initbot_core.state.factory import create_state_from_source
from initbot_core.state.state import State
from initbot_web.config import WebSettings
from initbot_web.routes.tracker import make_routes

_log = logging.getLogger(__name__)


async def _periodic_tasks(vuln_state: VulnerabilityState, state: State) -> None:
    while True:
        state.web_login_tokens.prune_expired()
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


def create_app(
    settings: WebSettings | None = None, web_url_path_prefix: str | None = None
) -> Starlette:
    cfg = settings or WebSettings()
    if not cfg.state.startswith("sqlite:"):
        raise SystemExit(f"initbot-web requires a SQLite state URI. Got: {cfg.state!r}")
    state = create_state_from_source(cfg.state)
    templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
    vuln_state = VulnerabilityState()
    url_path_prefix = (
        web_url_path_prefix or CORE_CFG.web_url_path_prefix or secrets.token_urlsafe(32)
    )

    @asynccontextmanager
    async def lifespan(_app: ASGIApp) -> AsyncGenerator[None, None]:
        task = create_task(_periodic_tasks(vuln_state, state))
        yield
        task.cancel()
        with suppress(CancelledError):
            await task

    # Ephemeral signing key: sessions are invalidated on app restart, which is acceptable.
    session_secret = secrets.token_urlsafe(32)
    https_only = bool(CORE_CFG.domain)
    admin_token = secrets.token_urlsafe(32)

    app = Starlette(
        routes=make_routes(state, templates, url_path_prefix, vuln_state, admin_token),
        middleware=[
            Middleware(
                SessionMiddleware,  # type: ignore[invalid-argument-type]  # SessionMiddleware satisfies _MiddlewareFactory
                secret_key=session_secret,
                https_only=https_only,
                same_site="lax",
            )
        ],
        lifespan=lifespan,
    )
    app.state.admin_token = admin_token
    app.state.url_path_prefix = url_path_prefix
    return app


def run() -> None:
    cfg = WebSettings(_cli_parse_args=True)  # type: ignore
    app = create_app(cfg)
    prefix = app.state.url_path_prefix
    admin_token = app.state.admin_token
    print(f"URL: http://localhost:{cfg.web_port}/{prefix}/{admin_token}/")
    if CORE_CFG.domain:
        print(f"External URL: https://{CORE_CFG.domain}/{prefix}/{admin_token}/")
    uvicorn.run(
        app,
        host=cfg.web_host,
        port=cfg.web_port,
    )
