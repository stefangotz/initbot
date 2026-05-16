# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
import secrets
from asyncio import (
    CancelledError,
    DatagramProtocol,
    Queue,
    QueueFull,
    create_task,
    get_running_loop,
    sleep,
)
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from typing import Any

import uvicorn
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.templating import Jinja2Templates
from starlette.types import ASGIApp

from initbot_core.config import CORE_CFG
from initbot_core.notify import send_notification
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


class _Notifier:
    """Broadcasts change notifications to registered SSE connections."""

    def __init__(self) -> None:
        self._queues: set[Queue[None]] = set()

    def register(self) -> Queue[None]:
        q: Queue[None] = Queue(maxsize=1)
        self._queues.add(q)
        return q

    def unregister(self, q: Queue[None]) -> None:
        self._queues.discard(q)

    def notify_all(self) -> None:
        for q in self._queues:
            with suppress(QueueFull):
                q.put_nowait(None)


class _UdpProtocol(DatagramProtocol):
    def __init__(self, notifier: _Notifier) -> None:
        self._notifier = notifier

    def datagram_received(self, data: bytes, addr: tuple[str | Any, int]) -> None:
        del data, addr
        self._notifier.notify_all()


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
    notifier = _Notifier()
    state = create_state_from_source(
        cfg.state,
        on_change=lambda: send_notification("127.0.0.1", cfg.notify_port),
    )
    templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
    vuln_state = VulnerabilityState()
    url_path_prefix = (
        web_url_path_prefix or CORE_CFG.web_url_path_prefix or secrets.token_urlsafe(32)
    )

    @asynccontextmanager
    async def lifespan(_app: ASGIApp) -> AsyncGenerator[None, None]:
        loop = get_running_loop()
        transport, _ = await loop.create_datagram_endpoint(
            lambda: _UdpProtocol(notifier),
            local_addr=("0.0.0.0", cfg.notify_port),  # noqa: S104  # all interfaces needed: receives from loopback and Docker internal network
        )
        task = create_task(_periodic_tasks(vuln_state, state))
        yield
        task.cancel()
        with suppress(CancelledError):
            await task
        transport.close()

    # Key rotation would be desirable (itsdangerous supports it via a list of secrets)
    # but Starlette's SessionMiddleware only accepts a single secret_key at this point.
    session_secret = state.session_secret.get_or_rotate()
    https_only = bool(CORE_CFG.domain)
    app = Starlette(
        routes=make_routes(state, templates, url_path_prefix, vuln_state),
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
    app.state.notifier = notifier
    app.state.url_path_prefix = url_path_prefix
    return app


def run() -> None:
    cfg = WebSettings(_cli_parse_args=True)  # type: ignore
    app = create_app(cfg)
    prefix = app.state.url_path_prefix
    print(f"Join URL: http://localhost:{cfg.web_port}/{prefix}/join/")
    if CORE_CFG.domain:
        print(f"External Join URL: https://{CORE_CFG.domain}/{prefix}/join/")
    uvicorn.run(
        app,
        host=cfg.web_host,
        port=cfg.web_port,
    )
