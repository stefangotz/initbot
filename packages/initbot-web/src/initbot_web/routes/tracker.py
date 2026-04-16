# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
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

_log = logging.getLogger(__name__)


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


def make_routes(  # pylint: disable=too-many-locals,too-many-statements
    state: State,
    templates: Jinja2Templates,
    url_path_prefix: str,
    vuln_state: VulnerabilityState,
    admin_token: str,
) -> list[Mount]:
    tracker_url = f"/{url_path_prefix}/tracker/"
    sse_url = f"/{url_path_prefix}/tracker/sse"
    set_initiative_url = f"/{url_path_prefix}/tracker/set-initiative"
    delete_character_url = f"/{url_path_prefix}/tracker/delete-character"

    async def login_page(request: Request) -> Response:
        """GET: validate token without consuming it; render auto-submit login form.

        Bots and link-preview crawlers (e.g. Discordbot) make GET requests but never
        submit forms, so the token is preserved for the actual user.
        """
        token = request.path_params["token"]
        _log.info(
            "login GET: scheme=%s x-forwarded-proto=%s",
            request.url.scheme,
            request.headers.get("x-forwarded-proto", "<absent>"),
        )
        is_player_token = state.web_login_tokens.find_valid(token) is not None
        is_admin_token = token == admin_token
        if not (is_player_token or is_admin_token):
            _log.warning("login GET: invalid or already-used token")
            return Response(status_code=403)
        return templates.TemplateResponse(request, "login.html", {})

    async def login_post(request: Request) -> Response:
        """POST: consume token, write session, redirect to tracker."""
        token = request.path_params["token"]
        discord_id = state.web_login_tokens.find_valid(token)
        if discord_id is not None:
            state.web_login_tokens.mark_used(token)
            player = state.players.get_from_discord_id(discord_id)
            _write_session(
                request, discord_id, player.name if player is not None else None
            )
            _log.info(
                "login POST: session written discord_id=%s session_keys=%s",
                discord_id,
                list(request.session.keys()),
            )
            return RedirectResponse(tracker_url, status_code=303)
        if token == admin_token:
            _write_session(request, None, None)
            _log.info(
                "login POST: admin session written session_keys=%s",
                list(request.session.keys()),
            )
            return RedirectResponse(tracker_url, status_code=303)
        _log.warning("login POST: invalid or already-used token")
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
                "set_initiative_url": set_initiative_url,
                "has_high_severity_vulnerabilities": vuln_state.has_high_severity_vulnerabilities,
            },
        )

    @datastar_response
    async def _tracker_sse(request: Request) -> AsyncGenerator[DatastarEvent, None]:
        last_snapshot: tuple[tuple[str, int | None], ...] = ()
        last_idle_snapshot: tuple[str, ...] = ()
        last_vuln = vuln_state.has_high_severity_vulnerabilities
        while not await request.is_disconnected():
            now = int(datetime.now().timestamp())
            all_chars = state.characters.get_all()
            chars = [
                c
                for c in all_chars
                if c.initiative is not None
                and c.last_used is not None
                and c.last_used > now - STALE_SECONDS
            ]
            chars.sort(key=lambda c: c.initiative or 0, reverse=True)
            idle_chars = [
                c
                for c in all_chars
                if c.initiative is None
                and c.last_used is not None
                and c.last_used > now - STALE_SECONDS
            ]
            idle_chars.sort(key=lambda c: c.name)

            chars_with_names = [(c, _resolve_player_name(state, c)) for c in chars]
            snapshot = tuple((c.name, c.initiative) for c, _ in chars_with_names)
            if snapshot != last_snapshot:
                last_snapshot = snapshot
                yield SSE.patch_elements(
                    _render_rows(chars_with_names, delete_character_url)
                )

            idle_with_names = [(c, _resolve_player_name(state, c)) for c in idle_chars]
            idle_snapshot = tuple(c.name for c in idle_chars)
            if idle_snapshot != last_idle_snapshot:
                last_idle_snapshot = idle_snapshot
                yield SSE.patch_elements(
                    _render_idle_rows(idle_with_names, delete_character_url)
                )

            current_vuln = vuln_state.has_high_severity_vulnerabilities
            if current_vuln != last_vuln:
                last_vuln = current_vuln
                yield SSE.patch_elements(_render_alert(current_vuln))

            await sleep(POLL_INTERVAL)

    async def tracker_sse(request: Request) -> Response:
        if (err := _require_auth(request)) is not None:
            return err
        return await _tracker_sse(request)

    @datastar_response
    async def _set_initiative(
        request: Request,
    ) -> DatastarEvent | tuple[()]:
        data = await request.json()
        char_name: str = data.get("editchar", "")
        try:
            initiative = int(data.get("initval", ""))
            if initiative < -99 or initiative > 99:
                return ()
            char = state.characters.get_from_name(char_name)
        except (TypeError, ValueError, KeyError):
            return ()
        char.initiative = initiative
        char.last_used = int(time.time())
        state.characters.update_and_store(char)
        return SSE.patch_signals({"editing": False})

    async def set_initiative(request: Request) -> Response:
        if (err := _require_auth(request)) is not None:
            return err
        return await _set_initiative(request)

    @datastar_response
    async def _delete_character(
        request: Request,
    ) -> DatastarEvent | tuple[()]:
        char_name: str = request.path_params.get("char_name", "")
        try:
            char = state.characters.get_from_name(char_name)
        except (TypeError, ValueError, KeyError):
            return ()
        state.character_actions.remove_all_for_character(char.name)
        state.characters.remove_and_store(char)
        return ()

    async def delete_character(request: Request) -> Response:
        if (err := _require_auth(request)) is not None:
            return err
        return await _delete_character(request)

    async def logout(request: Request) -> Response:
        request.session.clear()
        return Response(status_code=200)

    return [
        Mount(
            f"/{url_path_prefix}",
            routes=[
                Route("/tracker/", tracker_page),
                Route("/tracker/sse", tracker_sse),
                Route("/tracker/set-initiative", set_initiative, methods=["POST"]),
                Route(
                    "/tracker/delete-character/{char_name}",
                    delete_character,
                    methods=["POST"],
                ),
                Route("/logout", logout),
                Route("/{token}/", login_page, methods=["GET"]),
                Route("/{token}/", login_post, methods=["POST"]),
            ],
        )
    ]


def _resolve_player_name(state: State, cdi: CharacterData) -> str:
    return state.players.get_from_id(cdi.player_id).name


def _render_alert(has_high_severity_vulnerabilities: bool) -> str:
    content = (
        "<p>This application needs to receive a security update.</p>"
        if has_high_severity_vulnerabilities
        else ""
    )
    return f'<div id="security-alert">{content}</div>'


def _render_edit_button(char_name: str) -> str:
    safe = _safe_str(char_name)
    return (
        f'<button type="button" class="edit-btn" data-char="{safe}">\U0001f58a</button>'
    )


def _render_delete_button(char_name: str, delete_url_prefix: str) -> str:
    safe = _safe_str(char_name)
    return (
        f'<button type="button" class="del-btn"'
        f" data-on:click=\"@post('{delete_url_prefix}/{safe}')\">"
        f"\U0001f5d1</button>"
    )


def _render_rows(
    chars_with_names: list[tuple[CharacterData, str]], delete_url_prefix: str
) -> str:
    rows = "".join(
        f'<tr id="r{i}">'
        f"<td>{i + 1}</td>"
        f'<td><span class="init-val">{_safe_int(c.initiative)}</span>'
        f" {_render_edit_button(c.name)}</td>"
        f"<td>{_safe_str(c.name)}</td>"
        f"<td>{_safe_str(name)}</td>"
        f"<td>{_render_delete_button(c.name, delete_url_prefix)}</td>"
        f"</tr>"
        for i, (c, name) in enumerate(chars_with_names)
    )
    return f'<tbody id="initiative-rows">{rows}</tbody>'


def _render_idle_rows(
    chars_with_names: list[tuple[CharacterData, str]], delete_url_prefix: str
) -> str:
    rows = "".join(
        f"<tr>"
        f"<td>{_render_edit_button(c.name)}</td>"
        f"<td>{_safe_str(c.name)}</td>"
        f"<td>{_safe_str(name)}</td>"
        f"<td>{_render_delete_button(c.name, delete_url_prefix)}</td>"
        f"</tr>"
        for c, name in chars_with_names
    )
    return f'<tbody id="idle-rows">{rows}</tbody>'


def _safe_int(value: int | None) -> str:
    return re.sub(r"[^\d]", "", str(value))


def _safe_str(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9\xc0-\xd6\xd8-\xf6\xf8-\xff ]", "", value)
