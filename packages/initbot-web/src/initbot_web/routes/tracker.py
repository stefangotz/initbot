# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import re
import time
from asyncio import sleep
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Final

from datastar_py import ServerSentEventGenerator as SSE
from datastar_py.sse import DatastarEvent
from datastar_py.starlette import datastar_response
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.routing import Mount, Route
from starlette.templating import Jinja2Templates

from initbot_core.data.character import CharacterData
from initbot_core.security import VulnerabilityState
from initbot_core.state.state import State

POLL_INTERVAL = 1.5
STALE_SECONDS = 24 * 3600
SESSION_TTL: Final[int] = 8 * 3600


def make_routes(
    state: State,
    templates: Jinja2Templates,
    url_path_prefix: str,
    vuln_state: VulnerabilityState,
) -> list[Mount]:
    tracker_url = f"/{url_path_prefix}/tracker/"
    sse_url = f"/{url_path_prefix}/tracker/sse"

    def _require_auth(request: Request) -> Response | None:
        """Return a 403 Response if the session is missing or expired, else None."""
        if not request.session.get("authenticated"):
            return Response(status_code=403)
        expires_at = request.session.get("expires_at")
        if expires_at is None or time.time() > expires_at:
            request.session.clear()
            return Response(status_code=403)
        return None

    def _write_session(
        request: Request, discord_id: int | None, player_name: str | None
    ) -> None:
        request.session["authenticated"] = True
        request.session["discord_id"] = discord_id
        request.session["player_name"] = player_name
        request.session["expires_at"] = int(time.time()) + SESSION_TTL

    async def login_redirect(request: Request) -> Response:
        token = request.path_params["token"]
        discord_id = state.web_login_tokens.find_valid(token)
        if discord_id is not None:
            state.web_login_tokens.mark_used(token)
            player = state.players.get_from_discord_id(discord_id)
            _write_session(
                request, discord_id, player.name if player is not None else None
            )
            return RedirectResponse(tracker_url, status_code=302)
        if url_path_prefix and token == url_path_prefix:
            _write_session(request, None, None)
            return RedirectResponse(tracker_url, status_code=302)
        return Response(status_code=403)

    async def tracker_page(request: Request) -> Response:
        if (err := _require_auth(request)) is not None:
            return err
        player_name: str | None = request.session.get("player_name")
        return templates.TemplateResponse(
            request,
            "tracker.html",
            {
                "player_name": player_name,
                "sse_url": sse_url,
                "has_high_severity_vulnerabilities": vuln_state.has_high_severity_vulnerabilities,
            },
        )

    @datastar_response
    async def _tracker_sse(request: Request) -> AsyncGenerator[DatastarEvent, None]:
        last_snapshot: tuple[tuple[str, int | None], ...] = ()
        last_vuln = vuln_state.has_high_severity_vulnerabilities
        while not await request.is_disconnected():
            now = int(datetime.now().timestamp())
            chars = [
                c
                for c in state.characters.get_all()
                if c.initiative is not None
                and c.last_used is not None
                and c.last_used > now - STALE_SECONDS
            ]
            chars.sort(key=lambda c: c.initiative or 0, reverse=True)

            chars_with_names = [(c, _resolve_player_name(state, c)) for c in chars]
            snapshot = tuple((c.name, c.initiative) for c, _ in chars_with_names)
            if snapshot != last_snapshot:
                last_snapshot = snapshot
                yield SSE.patch_elements(_render_rows(chars_with_names))

            current_vuln = vuln_state.has_high_severity_vulnerabilities
            if current_vuln != last_vuln:
                last_vuln = current_vuln
                yield SSE.patch_elements(_render_alert(current_vuln))

            await sleep(POLL_INTERVAL)

    async def tracker_sse(request: Request) -> Response:
        if (err := _require_auth(request)) is not None:
            return err
        return await _tracker_sse(request)

    async def logout(request: Request) -> Response:
        request.session.clear()
        return Response(status_code=200)

    return [
        Mount(
            f"/{url_path_prefix}",
            routes=[
                Route("/tracker/", tracker_page),
                Route("/tracker/sse", tracker_sse),
                Route("/logout", logout),
                Route("/{token}/", login_redirect),
            ],
        )
    ]


def _resolve_player_name(state: State, cdi: CharacterData) -> str:
    if cdi.player_id is None:
        raise ValueError(f"Character {cdi.name!r} has no player_id")
    return state.players.get_from_id(cdi.player_id).name


def _render_alert(has_high_severity_vulnerabilities: bool) -> str:
    content = (
        "<p>This application needs to receive a security update.</p>"
        if has_high_severity_vulnerabilities
        else ""
    )
    return f'<div id="security-alert">{content}</div>'


def _render_rows(chars_with_names: list[tuple[CharacterData, str]]) -> str:
    rows = "".join(
        f'<tr id="r{i}"><td>{i + 1}</td><td>{_safe_int(c.initiative)}</td>'
        f"<td>{_safe_str(c.name)}</td><td>{_safe_str(name)}</td></tr>"
        for i, (c, name) in enumerate(chars_with_names)
    )
    return f'<tbody id="initiative-rows">{rows}</tbody>'


def _safe_int(value: int | None) -> str:
    return re.sub(r"[^\d]", "", str(value))


def _safe_str(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9\xc0-\xd6\xd8-\xf6\xf8-\xff ]", "", value)
