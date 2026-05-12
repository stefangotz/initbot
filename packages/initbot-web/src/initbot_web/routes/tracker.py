# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import html
import logging
import re
import secrets
import time
from collections.abc import AsyncGenerator, Sequence
from datetime import datetime
from typing import Final
from urllib.parse import quote

from datastar_py import ServerSentEventGenerator as SSE
from datastar_py.sse import DatastarEvent
from datastar_py.starlette import datastar_response
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.routing import Mount, Route
from starlette.templating import Jinja2Templates

from initbot_core.character_name import validate_character_name
from initbot_core.data.character import CharacterData, NewCharacterData
from initbot_core.data.player import PlayerData
from initbot_core.models.roll import DiceExpression
from initbot_core.security import VulnerabilityState
from initbot_core.state.state import State

STALE_SECONDS = 24 * 3600
SESSION_TTL: Final[int] = 8 * 3600
_INITIATIVE_INPUT_ERROR = (
    "Enter a number from \u221299 to 99, or a dice formula like d20+5."
)
_ADMIN_DISCORD_ID: Final[int] = 0
_ADMIN_PLAYER_NAME: Final[str] = "admin"
_NAME_INPUT_ERROR_EMPTY: Final[str] = "Enter a character name."
_NAME_INPUT_ERROR_EXISTS: Final[str] = "A character with this name already exists."
_NAME_INPUT_ERROR_INVALID: Final[str] = "Name contains characters that are not allowed."
_STALE_INIT: Final[str] = "⏳"  # ⏳

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
    request.session["session_key"] = secrets.token_urlsafe(16)


def _parse_initval(
    initval: str,
    allow_empty: bool = False,
) -> tuple[int | None, DatastarEvent] | tuple[int | None, None]:
    """Return (as_integer_or_None, None) on success, or (None, error_event) on failure."""
    if not initval:
        if allow_empty:
            return None, None
        return None, SSE.patch_signals({"editerror": _INITIATIVE_INPUT_ERROR})
    try:
        as_integer = int(initval)
        if as_integer < -99 or as_integer > 99:
            return None, SSE.patch_signals({"editerror": _INITIATIVE_INPUT_ERROR})
        return as_integer, None
    except ValueError:
        try:
            DiceExpression.create(initval)
            return None, None
        except ValueError:
            return None, SSE.patch_signals({"editerror": _INITIATIVE_INPUT_ERROR})


def _apply_edit(
    state: State,
    edit_char_name: str,
    new_char_name: str,
    editplayerid_str: str,
    initval: str,
) -> DatastarEvent | tuple[()] | CharacterData:
    """Validate and apply edit-mode changes; return char on success or a signal/no-op."""
    effective_name = new_char_name if new_char_name else edit_char_name
    try:
        effective_name = validate_character_name(effective_name)
    except ValueError:
        return SSE.patch_signals({"nameerror": _NAME_INPUT_ERROR_INVALID})
    as_integer, err = _parse_initval(initval, allow_empty=True)
    if err is not None:
        return err
    try:
        char = state.characters.get_from_name(edit_char_name)
    except (TypeError, ValueError, KeyError):
        return ()
    if effective_name != edit_char_name:
        try:
            char = state.characters.rename_and_store(char, effective_name)
        except ValueError:
            return SSE.patch_signals({"nameerror": _NAME_INPUT_ERROR_EXISTS})
    if editplayerid_str:
        try:
            new_player_id = int(editplayerid_str)
            state.players.get_from_id(new_player_id)
            char.player_id = new_player_id
        except (ValueError, KeyError):
            pass
    if as_integer is not None:
        char.initiative = as_integer
    elif initval:
        char.initiative_dice = initval
    return char


def _apply_create(
    state: State,
    discord_id: int | None,
    player_name: str | None,
    new_char_name: str,
    initval: str,
) -> DatastarEvent | tuple[()] | CharacterData:
    """Validate and create a new character; return char on success or a signal/no-op."""
    if not new_char_name:
        return ()
    try:
        new_char_name = validate_character_name(new_char_name)
    except ValueError:
        return SSE.patch_signals({"nameerror": _NAME_INPUT_ERROR_INVALID})
    as_integer, err = _parse_initval(initval)
    if err is not None:
        return err
    if discord_id is not None:
        player = state.players.get_from_discord_id(discord_id)
        if player is None:
            player = state.players.upsert(discord_id, player_name or "Player")
    else:
        player = state.players.upsert(_ADMIN_DISCORD_ID, _ADMIN_PLAYER_NAME)
    try:
        char = state.characters.add_store_and_get(
            NewCharacterData(name=new_char_name, player_id=player.id)
        )
    except ValueError:
        return SSE.patch_signals({"nameerror": _NAME_INPUT_ERROR_EXISTS})
    if as_integer is not None:
        char.initiative = as_integer
    else:
        char.initiative_dice = initval
    return char


def _is_initiative_eligible(char: CharacterData, now: int) -> bool:
    return (
        char.initiative is not None
        and char.last_used is not None
        and char.last_used > now - STALE_SECONDS
    )


def _compute_desired_ranked(all_chars: Sequence[CharacterData], now: int) -> list[str]:
    eligible = [c for c in all_chars if _is_initiative_eligible(c, now)]
    eligible.sort(key=lambda c: c.initiative, reverse=True)  # type: ignore[arg-type]
    return [c.name for c in eligible]


def make_routes(  # pylint: disable=too-many-locals,too-many-statements
    state: State,
    templates: Jinja2Templates,
    url_path_prefix: str,
    vuln_state: VulnerabilityState,
    admin_token: str,
) -> list[Mount]:
    tracker_url = f"/{url_path_prefix}/tracker/"
    sse_url = f"/{url_path_prefix}/tracker/sse"
    add_character_url = f"/{url_path_prefix}/tracker/add-character"
    roll_initiative_url = f"/{url_path_prefix}/tracker/roll-initiative"
    delete_character_url = f"/{url_path_prefix}/tracker/delete-character"
    resort_url = f"/{url_path_prefix}/tracker/resort"
    sort_state: list[int] = [0]
    # Per-browser-session sort versions: keyed by session_key (a random token
    # assigned at login). Incremented when a session makes an initiative change so
    # the originating browser auto-sorts without showing the stale indicator.
    session_sort_versions: dict[str, int] = {}

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
                "add_character_url": add_character_url,
                "has_high_severity_vulnerabilities": vuln_state.has_high_severity_vulnerabilities,
            },
        )

    @datastar_response
    async def _tracker_sse(request: Request) -> AsyncGenerator[DatastarEvent, None]:
        session_key: str = request.session.get("session_key", "")
        display_ranked: list[str] = []
        displayed_sort_version: int = -1
        displayed_session_version: int = -1
        last_is_stale: bool = False
        last_table_snapshot: tuple = ()
        last_player_snapshot: tuple[tuple[int, str], ...] = ()
        last_vuln = vuln_state.has_high_severity_vulnerabilities

        notify_q = request.app.state.notifier.register()
        notify_q.put_nowait(None)
        try:
            while not await request.is_disconnected():
                await notify_q.get()
                now = int(datetime.now().timestamp())
                all_chars = state.characters.get_all()
                all_players = state.players.get_all()
                players_by_id = {p.id: p for p in all_players}
                chars_by_name = {c.name: c for c in all_chars}

                desired_ranked = _compute_desired_ranked(all_chars, now)

                own_version = session_sort_versions.get(session_key, 0)
                if (
                    own_version > displayed_session_version
                    or sort_state[0] > displayed_sort_version
                ):
                    display_ranked = list(desired_ranked)
                    displayed_sort_version = sort_state[0]
                    displayed_session_version = own_version
                    is_stale = False
                    stale_names: frozenset[str] = frozenset()
                else:
                    display_ranked = [
                        n
                        for n in display_ranked
                        if n in chars_by_name
                        and _is_initiative_eligible(chars_by_name[n], now)
                    ]
                    is_stale = display_ranked != desired_ranked
                    if is_stale:
                        desired_index = {n: i for i, n in enumerate(desired_ranked)}
                        stale_names = frozenset(
                            n
                            for i, n in enumerate(display_ranked)
                            if desired_index.get(n, -1) != i
                        )
                    else:
                        stale_names = frozenset()

                ranked_set = set(display_ranked)
                bottom = sorted(
                    [c for c in all_chars if c.name not in ranked_set],
                    key=lambda c: c.last_used or 0,
                    reverse=True,
                )
                ranked_count = len(display_ranked)
                full_order: list[tuple[CharacterData, str]] = [
                    (
                        chars_by_name[n],
                        _resolve_player_name(players_by_id, chars_by_name[n]),
                    )
                    for n in display_ranked
                ] + [(c, _resolve_player_name(players_by_id, c)) for c in bottom]

                table_snapshot: tuple = (
                    tuple(display_ranked),
                    stale_names,
                    tuple(
                        (c.name, c.initiative, c.initiative_dice, pname)
                        for c, pname in full_order
                    ),
                )
                if table_snapshot != last_table_snapshot:
                    last_table_snapshot = table_snapshot
                    yield SSE.patch_elements(
                        _render_combined_rows(
                            full_order,
                            ranked_count,
                            stale_names,
                            roll_initiative_url,
                            delete_character_url,
                        )
                    )

                if is_stale != last_is_stale:
                    last_is_stale = is_stale
                    yield SSE.patch_elements(
                        _render_sort_indicator(is_stale, resort_url)
                    )

                players = [p for p in all_players if p.discord_id != _ADMIN_DISCORD_ID]
                player_snapshot = tuple((p.id, p.name) for p in players)
                if player_snapshot != last_player_snapshot:
                    last_player_snapshot = player_snapshot
                    yield SSE.patch_elements(_render_player_select(players))

                current_vuln = vuln_state.has_high_severity_vulnerabilities
                if current_vuln != last_vuln:
                    last_vuln = current_vuln
                    yield SSE.patch_elements(_render_alert(current_vuln))
        finally:
            request.app.state.notifier.unregister(notify_q)

    async def tracker_sse(request: Request) -> Response:
        if (err := _require_auth(request)) is not None:
            return err
        return await _tracker_sse(request)

    @datastar_response
    async def _add_character(
        request: Request,
    ) -> DatastarEvent | tuple[()]:
        data = await request.json()
        edit_char_name: str = str(data.get("editchar", "")).strip()
        initval: str = str(data.get("initval", "")).strip()
        if edit_char_name:
            result = _apply_edit(
                state,
                edit_char_name,
                str(data.get("newcharname", "")).strip(),
                str(data.get("editplayerid", "")).strip(),
                initval,
            )
        else:
            result = _apply_create(
                state,
                request.session.get("discord_id"),
                request.session.get("player_name"),
                str(data.get("newcharname", "")).strip(),
                initval,
            )
        if not isinstance(result, CharacterData):
            return result
        result.last_used = int(time.time())
        state.characters.update_and_store(result)
        _sk = request.session.get("session_key", "")
        session_sort_versions[_sk] = session_sort_versions.get(_sk, 0) + 1
        return SSE.patch_signals({
            "editing": False,
            "creating": False,
            "editerror": "",
            "nameerror": "",
        })

    async def add_character(request: Request) -> Response:
        if (err := _require_auth(request)) is not None:
            return err
        return await _add_character(request)

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

    @datastar_response
    async def _roll_initiative(
        request: Request,
    ) -> DatastarEvent | tuple[()]:
        char_name: str = request.path_params.get("char_name", "")
        try:
            char = state.characters.get_from_name(char_name)
        except (TypeError, ValueError, KeyError):
            return ()
        initiative_dice = char.initiative_dice
        if not initiative_dice or not _has_valid_dice(initiative_dice):
            return ()
        char.initiative = DiceExpression.create(initiative_dice).roll_one()
        char.last_used = int(time.time())
        state.characters.update_and_store(char)
        _sk = request.session.get("session_key", "")
        session_sort_versions[_sk] = session_sort_versions.get(_sk, 0) + 1
        return ()

    async def roll_initiative(request: Request) -> Response:
        if (err := _require_auth(request)) is not None:
            return err
        return await _roll_initiative(request)

    @datastar_response
    async def _resort_initiative(
        request: Request,
    ) -> DatastarEvent | tuple[()]:
        sort_state[0] += 1
        request.app.state.notifier.notify_all()
        return ()

    async def resort_initiative(request: Request) -> Response:
        if (err := _require_auth(request)) is not None:
            return err
        return await _resort_initiative(request)

    async def logout(request: Request) -> Response:
        request.session.clear()
        return Response(status_code=200)

    return [
        Mount(
            f"/{url_path_prefix}",
            routes=[
                Route("/tracker/", tracker_page),
                Route("/tracker/sse", tracker_sse),
                Route("/tracker/add-character", add_character, methods=["POST"]),
                Route(
                    "/tracker/roll-initiative/{char_name}",
                    roll_initiative,
                    methods=["POST"],
                ),
                Route(
                    "/tracker/delete-character/{char_name}",
                    delete_character,
                    methods=["POST"],
                ),
                Route("/tracker/resort", resort_initiative, methods=["POST"]),
                Route("/logout", logout),
                Route("/{token}/", login_page, methods=["GET"]),
                Route("/{token}/", login_post, methods=["POST"]),
            ],
        )
    ]


def _resolve_player_name(
    players_by_id: dict[int, PlayerData], cdi: CharacterData
) -> str:
    player = players_by_id.get(cdi.player_id)
    return player.name if player is not None else "?"


def _render_alert(has_high_severity_vulnerabilities: bool) -> str:
    content = (
        "<p>This application needs to receive a security update.</p>"
        if has_high_severity_vulnerabilities
        else ""
    )
    return f'<div id="security-alert">{content}</div>'


def _render_player_select(players: Sequence[PlayerData]) -> str:
    options = "".join(
        f'<option value="{p.id}">{html.escape(p.name)}</option>' for p in players
    )
    return (
        f'<select id="player-select" data-bind:editplayerid '
        f'data-show="!$creating" style="display:none">'
        f"{options}</select>"
    )


def _has_valid_dice(initiative_dice: str | None) -> bool:
    if not initiative_dice:
        return False
    try:
        DiceExpression.create(initiative_dice)
        return True
    except ValueError:
        return False


_ROLL_BTN_TITLE = (
    "Roll initiative using this character's dice formula. "
    "Requires initiative dice to be set (e.g. d20+3). "
    "Equivalent to $init without specifying a value."
)
_EDIT_BTN_TITLE = (
    "Set this character's initiative. "
    "Enter a number (e.g. 17) or a dice formula (e.g. d20+3). "
    "Equivalent to the $init command."
)
_DELETE_BTN_TITLE = (
    "Remove this character from the tracker. Equivalent to the $remove command."
)


def _render_roll_button(char_name: str, roll_url_prefix: str) -> str:
    encoded = quote(char_name, safe="")
    return (
        f'<button type="button" class="roll-btn" title="{_ROLL_BTN_TITLE}"'
        f" data-on:click=\"@post('{roll_url_prefix}/{encoded}')\">"
        f"\U0001f3b2</button>"
    )


def _render_edit_button(char_name: str, player_id: int) -> str:
    escaped = html.escape(char_name, quote=True)
    return (
        f'<button type="button" class="edit-btn" title="{_EDIT_BTN_TITLE}"'
        f' data-char="{escaped}" data-playerid="{player_id}">\U0001f58a</button>'
    )


def _render_delete_button(char_name: str, delete_url_prefix: str) -> str:
    encoded = quote(char_name, safe="")
    return (
        f'<button type="button" class="del-btn" title="{_DELETE_BTN_TITLE}"'
        f" data-on:click=\"@post('{delete_url_prefix}/{encoded}')\">"
        f"\U0001f5d1</button>"
    )


def _render_sort_indicator(is_stale: bool, resort_url: str) -> str:
    if not is_stale:
        return '<div id="sort-indicator"></div>'
    return (
        f'<div id="sort-indicator">'
        f'<button type="button" class="resort-btn"'
        f" data-on:click=\"@post('{resort_url}')\">"
        f"Update initiatives"
        f"</button>"
        f"</div>"
    )


def _render_combined_rows(
    chars_with_names: list[tuple[CharacterData, str]],
    ranked_count: int,
    stale_names: frozenset[str],
    roll_url_prefix: str,
    delete_url_prefix: str,
) -> str:
    rows = []
    for i, (c, player_name) in enumerate(chars_with_names):
        separator = ' class="group-separator"' if i == ranked_count > 0 else ""
        init_cell = _STALE_INIT if c.name in stale_names else _safe_int(c.initiative)
        roll_btn = (
            _render_roll_button(c.name, roll_url_prefix)
            if _has_valid_dice(c.initiative_dice)
            else ""
        )
        rows.append(
            f"<tr{separator}>"
            f"<td>{html.escape(c.name)}</td>"
            f"<td>{html.escape(player_name)}</td>"
            f"<td>{init_cell}</td>"
            f"<td>{_safe_dice(c.initiative_dice)}</td>"
            f"<td>{_render_edit_button(c.name, c.player_id)}</td>"
            f"<td>{roll_btn}</td>"
            f"<td>{_render_delete_button(c.name, delete_url_prefix)}</td>"
            f"</tr>"
        )
    return f'<tbody id="char-rows">{"".join(rows)}</tbody>'


def _safe_int(value: int | None) -> str:
    if value is None:
        return ""
    return str(int(value))


def _safe_dice(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[^a-zA-Z0-9+\-*/() ]", "", value)
