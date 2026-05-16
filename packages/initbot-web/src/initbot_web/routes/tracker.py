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
from typing import Final, NamedTuple
from urllib.parse import quote

from datastar_py import ServerSentEventGenerator as SSE
from datastar_py.sse import DatastarEvent, SignalValue
from datastar_py.starlette import datastar_response
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.routing import Mount, Route
from starlette.templating import Jinja2Templates

from initbot_core.character_name import validate_character_name
from initbot_core.data.character import CharacterData, NewCharacterData
from initbot_core.data.player import PlayerData
from initbot_core.models.roll import parse_dice_spec
from initbot_core.security import VulnerabilityState
from initbot_core.state.state import State

STALE_SECONDS = 24 * 3600
SESSION_TTL: Final[int] = 8 * 3600
_INITIATIVE_INPUT_ERROR = (
    "Enter a number from \u221299 to 99, or a dice formula like d20+5 or d20adv."
)
_NAME_INPUT_ERROR_EMPTY: Final[str] = "Enter a character name."
_NAME_INPUT_ERROR_EXISTS: Final[str] = "A character with this name already exists."
_NAME_INPUT_ERROR_INVALID: Final[str] = "Name contains characters that are not allowed."
_STALE_INIT: Final[str] = "⏳"  # ⏳

# Datastar signal name constants — must match the keys in tracker.html data-signals
# and data-bind attributes.
_SIG_EDITCHAR: Final[str] = "editchar"
_SIG_EDITINGFIELD: Final[str] = "editingfield"
_SIG_NEXTCHAR: Final[str] = "nextchar"
_SIG_NEXTFIELD: Final[str] = "nextfield"
_SIG_INITVAL: Final[str] = "initval"
_SIG_EDITERROR: Final[str] = "editerror"
_SIG_NAMEERROR: Final[str] = "nameerror"
_SIG_EDITPLAYERID: Final[str] = "editplayerid"
_SIG_CREATING: Final[str] = "creating"
_SIG_NEWCHARNAME: Final[str] = "newcharname"

_log = logging.getLogger(__name__)


class _SessionPlayer(NamedTuple):
    """Player identity extracted from the session for use in character operations."""

    player_id: int | None
    discord_id: int | None
    player_name: str | None

    @classmethod
    def from_session(cls, request: Request) -> "_SessionPlayer":
        return cls(
            player_id=request.session.get("player_id"),
            discord_id=request.session.get("discord_id"),
            player_name=request.session.get("player_name"),
        )


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
    request: Request,
    discord_id: int | None,
    player_name: str | None,
    player_id: int | None = None,
) -> None:
    request.session["authenticated"] = True
    request.session["discord_id"] = discord_id
    request.session["player_name"] = player_name
    request.session["player_id"] = player_id
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
        return None, SSE.patch_signals({_SIG_EDITERROR: _INITIATIVE_INPUT_ERROR})
    try:
        as_integer = int(initval)
        if as_integer < -99 or as_integer > 99:
            return None, SSE.patch_signals({_SIG_EDITERROR: _INITIATIVE_INPUT_ERROR})
        return as_integer, None
    except ValueError:
        try:
            parse_dice_spec(initval)
            return None, None
        except ValueError:
            return None, SSE.patch_signals({_SIG_EDITERROR: _INITIATIVE_INPUT_ERROR})


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
        return SSE.patch_signals({_SIG_NAMEERROR: _NAME_INPUT_ERROR_INVALID})
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
            return SSE.patch_signals({_SIG_NAMEERROR: _NAME_INPUT_ERROR_EXISTS})
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
    session_player: _SessionPlayer,
    new_char_name: str,
    initval: str,
) -> DatastarEvent | tuple[()] | CharacterData:
    """Validate and create a new character; return char on success or a signal/no-op."""
    if not new_char_name:
        return ()
    try:
        new_char_name = validate_character_name(new_char_name)
    except ValueError:
        return SSE.patch_signals({_SIG_NAMEERROR: _NAME_INPUT_ERROR_INVALID})
    as_integer, err = _parse_initval(initval)
    if err is not None:
        return err
    if session_player.player_id is not None:
        player = state.players.get_from_id(session_player.player_id)
    elif session_player.discord_id is not None:
        player = state.players.get_from_discord_id(session_player.discord_id)
        if player is None:
            player = state.players.upsert_discord(
                session_player.discord_id,
                session_player.player_name or "Player",
            )
    else:
        return ()
    try:
        char = state.characters.add_store_and_get(
            NewCharacterData(name=new_char_name, player_id=player.id)
        )
    except ValueError:
        return SSE.patch_signals({_SIG_NAMEERROR: _NAME_INPUT_ERROR_EXISTS})
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
    eligible.sort(key=lambda c: c.initiative, reverse=True)
    return [c.name for c in eligible]


def make_routes(  # pylint: disable=too-many-locals,too-many-statements
    state: State,
    templates: Jinja2Templates,
    url_path_prefix: str,
    vuln_state: VulnerabilityState,
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
        if state.web_login_tokens.find_valid(token) is None:
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
                request,
                discord_id,
                player.name if player is not None else None,
                player.id if player is not None else None,
            )
            _log.info(
                "login POST: session written discord_id=%s session_keys=%s",
                discord_id,
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
        last_player_snapshot: tuple = ()
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

                players = list(all_players)
                player_snapshot = tuple((p.id, p.name) for p in players)

                table_snapshot: tuple = (
                    tuple(display_ranked),
                    stale_names,
                    tuple(
                        (c.name, c.initiative, c.initiative_dice, pname)
                        for c, pname in full_order
                    ),
                )
                if (
                    table_snapshot != last_table_snapshot
                    or player_snapshot != last_player_snapshot
                ):
                    last_table_snapshot = table_snapshot
                    last_player_snapshot = player_snapshot
                    yield SSE.patch_elements(
                        _render_combined_rows(
                            full_order,
                            ranked_count,
                            stale_names,
                            roll_initiative_url,
                            delete_character_url,
                            players,
                            add_character_url,
                        )
                    )

                if is_stale != last_is_stale:
                    last_is_stale = is_stale
                    yield SSE.patch_elements(
                        _render_sort_indicator(is_stale, resort_url)
                    )

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
        edit_char_name: str = str(data.get(_SIG_EDITCHAR, "")).strip()
        initval: str = str(data.get(_SIG_INITVAL, "")).strip()
        if edit_char_name:
            result = _apply_edit(
                state,
                edit_char_name,
                str(data.get(_SIG_NEWCHARNAME, "")).strip(),
                str(data.get(_SIG_EDITPLAYERID, "")).strip(),
                initval,
            )
        else:
            result = _apply_create(
                state,
                _SessionPlayer.from_session(request),
                str(data.get(_SIG_NEWCHARNAME, "")).strip(),
                initval,
            )
        if not isinstance(result, CharacterData):
            return result
        result.last_used = int(time.time())
        state.characters.update_and_store(result)
        _sk = request.session.get("session_key", "")
        session_sort_versions[_sk] = session_sort_versions.get(_sk, 0) + 1
        nextchar: str = str(data.get(_SIG_NEXTCHAR, "")).strip()
        nextfield: str = str(data.get(_SIG_NEXTFIELD, "")).strip()
        if nextfield:
            try:
                next_c = (
                    state.characters.get_from_name(nextchar) if nextchar else result
                )
            except (KeyError, ValueError, TypeError):
                next_c = result
            extra: dict[str, SignalValue] = {}
            if nextfield == "player":
                extra[_SIG_EDITPLAYERID] = str(next_c.player_id)
            elif nextfield == "init":
                extra[_SIG_INITVAL] = (
                    str(next_c.initiative) if next_c.initiative is not None else ""
                )
            elif nextfield == "dice":
                extra[_SIG_INITVAL] = next_c.initiative_dice or ""
            elif nextfield == "name":
                extra[_SIG_NEWCHARNAME] = next_c.name
            return SSE.patch_signals(
                {
                    _SIG_EDITCHAR: next_c.name,
                    _SIG_EDITINGFIELD: nextfield,
                    _SIG_NEXTCHAR: "",
                    _SIG_NEXTFIELD: "",
                    _SIG_EDITERROR: "",
                    _SIG_NAMEERROR: "",
                }
                | extra
            )
        return SSE.patch_signals({
            _SIG_EDITCHAR: "",
            _SIG_EDITINGFIELD: "",
            _SIG_CREATING: False,
            _SIG_NEXTCHAR: "",
            _SIG_NEXTFIELD: "",
            _SIG_EDITERROR: "",
            _SIG_NAMEERROR: "",
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
        char.initiative = parse_dice_spec(initiative_dice).roll_one()
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

    async def join_page(request: Request) -> Response:
        """GET: render the standalone player name-entry form."""
        return templates.TemplateResponse(request, "join.html", {"error": ""})

    async def join_post(request: Request) -> Response:
        """POST: find or create a standalone player, write session, redirect to tracker."""
        form = await request.form()
        name = str(form.get("name", "")).strip()
        if not name:
            return templates.TemplateResponse(
                request, "join.html", {"error": "Enter your name."}
            )
        result = state.players.upsert_standalone(name)
        if isinstance(result, str):
            return templates.TemplateResponse(
                request, "join.html", {"error": "That name is already in use."}
            )
        _write_session(request, None, result.name, result.id)
        _log.info(
            "join POST: session written player_id=%s session_keys=%s",
            result.id,
            list(request.session.keys()),
        )
        return RedirectResponse(tracker_url, status_code=303)

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
                Route("/join/", join_page, methods=["GET"]),
                Route("/join/", join_post, methods=["POST"]),
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


def _render_player_options(players: Sequence[PlayerData]) -> str:
    return "".join(
        f'<option value="{p.id}">{html.escape(p.name)}</option>' for p in players
    )


def _has_valid_dice(initiative_dice: str | None) -> bool:
    if not initiative_dice:
        return False
    try:
        parse_dice_spec(initiative_dice)
        return True
    except ValueError:
        return False


_ROLL_BTN_TITLE = (
    "Roll initiative using this character's dice formula. "
    "Requires initiative dice to be set (e.g. d20+3 or d20adv). "
    "Equivalent to $init without specifying a value."
)
_DELETE_BTN_TITLE = (
    "Remove this character from the tracker. Equivalent to the $remove command."
)


def _render_roll_button(char_name: str, roll_url_prefix: str) -> str:
    encoded = quote(char_name, safe="")
    tab = "evt.key==='Tab'&&(evt.preventDefault(),el.closest('tr').querySelector('.del-btn')?.focus())"
    return (
        f'<button type="button" class="roll-btn" title="{_ROLL_BTN_TITLE}"'
        f" data-on:click=\"@post('{roll_url_prefix}/{encoded}')\""
        f' data-on:keydown="{tab}"'
        f" data-on:focus=\"$editchar=''\">"
        f"\U0001f3b2</button>"
    )


def _render_delete_button(char_name: str, delete_url_prefix: str) -> str:
    encoded = quote(char_name, safe="")
    tab = (
        "evt.key==='Tab'&&(evt.preventDefault(),"
        "$editchar=el.closest('tr').dataset.char,"
        "$editingfield='init',"
        "$initval=el.closest('tr').dataset.initval,"
        "$newcharname='',$editplayerid='',$editerror='',$nameerror='',$creating=false)"
    )
    return (
        f'<button type="button" class="del-btn" title="{_DELETE_BTN_TITLE}"'
        f" data-on:click=\"@post('{delete_url_prefix}/{encoded}')\""
        f' data-on:keydown="{tab}"'
        f" data-on:focus=\"$editchar=''\">"
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


def _inline_click_switch(next_field: str, add_url: str, direct_open: str) -> str:
    """Return a data-on:click expression for clicking a cell while another may be open.

    If an edit is active the click saves it first (POST), then opens next_field.
    The guard `!($editingfield==='name'&&$newcharname==='')` skips the POST when
    the name input is open but empty — matching the Escape-without-save semantics
    that apply to empty name edits.  In all other cases (including empty init/dice)
    the POST is sent and the server decides whether to accept or reject the value.
    """
    save_and_switch = (
        f"($nextchar=el.closest('tr').dataset.char,"
        f"$nextfield='{next_field}',@post('{add_url}'))"
    )
    return (
        f"$editchar!==''&&!($editingfield==='name'&&$newcharname==='')"
        f"?{save_and_switch}"
        f":{direct_open}"
    )


def _inline_blur(field: str) -> str:
    """Return a data-on:blur expression that cancels the edit only when this field is active.

    The $nextfield==='' guard prevents cancellation during a save-and-switch sequence,
    where focus temporarily leaves the input while the POST is in flight.
    """
    return (
        f"setTimeout(()=>{{"
        f"if(el.closest('tr').dataset.char===$editchar"
        f"&&$editingfield==='{field}'"
        f"&&$nextfield===''"
        f"&&!el.closest('td').contains(document.activeElement))"
        f"{{$editchar='';$editingfield='';$editerror='';$nameerror='';}}"
        f"}},0)"
    )


def _render_inline_name_cell(char_name: str, add_url: str) -> str:
    safe_name = html.escape(char_name)
    field = "name"
    span_show = f"el.closest('tr').dataset.char!==$editchar||$editingfield!=='{field}'"
    input_show = f"el.closest('tr').dataset.char===$editchar&&$editingfield==='{field}'"
    direct_open = (
        f"($editchar=el.closest('tr').dataset.char,$editingfield='{field}',"
        f"$newcharname=el.closest('tr').dataset.char,$initval='',"
        f"$editplayerid='',$editerror='',$nameerror='',$creating=false)"
    )
    click = _inline_click_switch(field, add_url, direct_open)
    keydown = (
        f"evt.key==='Escape'?($editchar='',$editingfield='',$editerror='',$nameerror=''):"
        f"evt.key==='Tab'?(evt.preventDefault(),"
        f"$newcharname===''?"
        f"($editingfield='player',$editplayerid=el.closest('tr').dataset.playerid):"
        f"($editingfield='player',$editplayerid=el.closest('tr').dataset.playerid,"
        f"$nextfield='player',@post('{add_url}'))):"
        f"(evt.key==='Enter'&&($newcharname===''?"
        f"($editchar='',$editingfield='',$editerror='',$nameerror=''):"
        f"@post('{add_url}')))"
    )
    blur = _inline_blur(field)
    effect = f"({input_show})&&setTimeout(()=>el.focus(),0)"
    error_show = f"{input_show}&&$nameerror"
    return (
        f"<td>"
        f'<span class="editable" data-show="{span_show}" data-on:click="{click}">'
        f"{safe_name}</span>"
        f'<input class="inline-input" type="text" data-bind:newcharname'
        f' data-show="{input_show}" style="display:none"'
        f' maxlength="32" autocomplete="off" placeholder="Character name"'
        f' data-effect="{effect}"'
        f' data-on:keydown="{keydown}"'
        f' data-on:blur="{blur}">'
        f'<span class="field-error" data-show="{error_show}"'
        f' data-text="$nameerror" style="display:none"></span>'
        f"</td>"
    )


def _render_inline_player_cell(
    player_name: str,
    players: Sequence[PlayerData],
    add_url: str,
) -> str:
    safe_player = html.escape(player_name)
    options = _render_player_options(players)
    field = "player"
    span_show = f"el.closest('tr').dataset.char!==$editchar||$editingfield!=='{field}'"
    select_show = (
        f"el.closest('tr').dataset.char===$editchar&&$editingfield==='{field}'"
    )
    direct_open = (
        f"($editchar=el.closest('tr').dataset.char,$editingfield='{field}',"
        f"$editplayerid=el.closest('tr').dataset.playerid,"
        f"$newcharname='',$initval='',$editerror='',$nameerror='',$creating=false)"
    )
    click = _inline_click_switch(field, add_url, direct_open)
    # Tab moves to dice; $initval is left empty here and pre-filled by the server
    # response (nextfield='dice' causes the server to return initval=dice formula).
    select_keydown = (
        f"evt.key==='Tab'&&$editchar!==''?(evt.preventDefault(),"
        f"$editingfield='dice',"
        f"$nextfield='dice',@post('{add_url}')):"
        f"(evt.key==='Escape'&&($editchar='',$editingfield=''))"
    )
    blur = (
        f"setTimeout(()=>{{"
        f"if(el.closest('tr').dataset.char===$editchar"
        f"&&$editingfield==='{field}'"
        f"&&$nextfield===''"
        f"&&!el.closest('td').contains(document.activeElement))"
        f"{{$editchar='';$editingfield='';}}"
        f"}},0)"
    )
    effect = f"({select_show})&&setTimeout(()=>el.focus(),0)"
    return (
        f"<td>"
        f'<span class="editable" data-show="{span_show}" data-on:click="{click}">'
        f"{safe_player}</span>"
        f'<select class="inline-select" data-bind:editplayerid'
        f' data-show="{select_show}" style="display:none"'
        f' data-effect="{effect}"'
        f" data-on:change=\"@post('{add_url}')\""
        f' data-on:keydown="{select_keydown}"'
        f' data-on:blur="{blur}">'
        f"{options}</select>"
        f"</td>"
    )


def _render_inline_init_cell(init_display: str, add_url: str) -> str:
    field = "init"
    span_class = "editable editable-empty" if init_display == "—" else "editable"
    span_show = f"el.closest('tr').dataset.char!==$editchar||$editingfield!=='{field}'"
    input_show = f"el.closest('tr').dataset.char===$editchar&&$editingfield==='{field}'"
    direct_open = (
        f"($editchar=el.closest('tr').dataset.char,$editingfield='{field}',"
        f"$initval=el.closest('tr').dataset.initval,"
        f"$newcharname='',$editplayerid='',$editerror='',$nameerror='',$creating=false)"
    )
    click = _inline_click_switch(field, add_url, direct_open)
    keydown = (
        f"evt.key==='Escape'?($editchar='',$editingfield='',$editerror=''):"
        f"evt.key==='Tab'?(evt.preventDefault(),"
        f"$editingfield='name',$newcharname=el.closest('tr').dataset.char,"
        f"$nextfield='name',@post('{add_url}')):"
        f"(evt.key==='Enter'&&@post('{add_url}'))"
    )
    blur = _inline_blur(field)
    effect = f"({input_show})&&setTimeout(()=>el.focus(),0)"
    error_show = f"{input_show}&&$editerror"
    return (
        f"<td>"
        f'<span class="{span_class}" data-show="{span_show}" data-on:click="{click}">'
        f"{init_display}</span>"
        f'<input class="inline-input" type="text" data-bind:initval'
        f' data-show="{input_show}" style="display:none"'
        f' autocomplete="off" placeholder="e.g. 17, d20+3, or d20adv"'
        f' data-effect="{effect}"'
        f' data-on:keydown="{keydown}"'
        f' data-on:blur="{blur}">'
        f'<span class="field-error" data-show="{error_show}"'
        f' data-text="$editerror" style="display:none"></span>'
        f"</td>"
    )


def _render_inline_dice_cell(initiative_dice: str | None, add_url: str) -> str:
    display = _safe_dice(initiative_dice) or "—"
    field = "dice"
    span_class = "editable editable-empty" if display == "—" else "editable"
    span_show = f"el.closest('tr').dataset.char!==$editchar||$editingfield!=='{field}'"
    input_show = f"el.closest('tr').dataset.char===$editchar&&$editingfield==='{field}'"
    direct_open = (
        f"($editchar=el.closest('tr').dataset.char,$editingfield='{field}',"
        f"$initval=el.closest('tr').dataset.diceval,"
        f"$newcharname='',$editplayerid='',$editerror='',$nameerror='',$creating=false)"
    )
    click = _inline_click_switch(field, add_url, direct_open)
    keydown = (
        f"evt.key==='Escape'?($editchar='',$editingfield='',$editerror=''):"
        f"evt.key==='Tab'?(evt.preventDefault(),"
        f"$editingfield='',"
        f"@post('{add_url}'),"
        f"setTimeout(()=>(el.closest('tr').querySelector('.roll-btn')"
        f"||el.closest('tr').querySelector('.del-btn'))?.focus(),0)):"
        f"(evt.key==='Enter'&&@post('{add_url}'))"
    )
    blur = _inline_blur(field)
    effect = f"({input_show})&&setTimeout(()=>el.focus(),0)"
    error_show = f"{input_show}&&$editerror"
    return (
        f"<td>"
        f'<span class="{span_class}" data-show="{span_show}" data-on:click="{click}">'
        f"{display}</span>"
        f'<input class="inline-input" type="text" data-bind:initval'
        f' data-show="{input_show}" style="display:none"'
        f' autocomplete="off" placeholder="e.g. d20+3 or d20adv"'
        f' data-effect="{effect}"'
        f' data-on:keydown="{keydown}"'
        f' data-on:blur="{blur}">'
        f'<span class="field-error" data-show="{error_show}"'
        f' data-text="$editerror" style="display:none"></span>'
        f"</td>"
    )


def _render_combined_rows(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    chars_with_names: list[tuple[CharacterData, str]],
    ranked_count: int,
    stale_names: frozenset[str],
    roll_url_prefix: str,
    delete_url_prefix: str,
    players: Sequence[PlayerData],
    add_character_url: str,
) -> str:
    rows = []
    for i, (c, player_name) in enumerate(chars_with_names):
        if i == ranked_count > 0:
            row_class = ' class="group-separator idle"'
        elif i > ranked_count > 0:
            row_class = ' class="idle"'
        else:
            row_class = ""
        init_display = (
            _STALE_INIT if c.name in stale_names else (_safe_int(c.initiative) or "—")
        )
        roll_btn = (
            _render_roll_button(c.name, roll_url_prefix)
            if _has_valid_dice(c.initiative_dice)
            else ""
        )
        rows.append(
            f"<tr{row_class}"
            f' data-char="{html.escape(c.name, quote=True)}"'
            f' data-playerid="{c.player_id}"'
            f' data-initval="{_safe_int(c.initiative) or ""}"'
            f' data-diceval="{html.escape(_safe_dice(c.initiative_dice), quote=True)}">'
            + _render_inline_init_cell(init_display, add_character_url)
            + _render_inline_name_cell(c.name, add_character_url)
            + _render_inline_player_cell(player_name, players, add_character_url)
            + _render_inline_dice_cell(c.initiative_dice, add_character_url)
            + f"<td>{roll_btn}</td>"
            + f"<td>{_render_delete_button(c.name, delete_url_prefix)}</td>"
            + "</tr>"
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
