# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from collections.abc import Callable, Iterable
from typing import Any, Final

from discord.ext import commands
from discord.ext.commands import Context

from initbot_core.config import CORE_CFG
from initbot_core.data.character import CharacterData
from initbot_core.data.player import PlayerData
from initbot_core.state.state import State


def _require_state(
    get_collection: Callable[[State], Any], label: str
) -> Callable[..., Any]:
    def predicate(ctx: commands.Context) -> bool:
        if not get_collection(ctx.bot.initbot_state).get_all():
            raise commands.CheckFailure(
                f"This command requires {label} data, which has not been loaded."
            )
        return True

    return commands.check(predicate)


abilities_required: Final[Callable[..., Any]] = _require_state(
    lambda s: s.abilities, "ability"
)
augurs_required: Final[Callable[..., Any]] = _require_state(lambda s: s.augurs, "augur")
classes_required: Final[Callable[..., Any]] = _require_state(
    lambda s: s.classes, "class"
)
occupations_required: Final[Callable[..., Any]] = _require_state(
    lambda s: s.occupations, "occupation"
)
crits_required: Final[Callable[..., Any]] = _require_state(
    lambda s: s.crits, "crit table"
)


def _web_configured(_ctx: commands.Context) -> bool:
    if not (CORE_CFG.domain and CORE_CFG.web_url_path_prefix):
        raise commands.CheckFailure(
            "The web command is not available (DOMAIN or WEB_URL_PATH_PREFIX not configured)."
        )
    return True


web_configured: Final[Callable[..., Any]] = commands.check(_web_configured)


def sync_player(state: State, ctx: Context) -> PlayerData:
    """Upsert the player record and backfill player_id on their legacy characters."""
    player = state.players.upsert(discord_id=ctx.author.id, name=ctx.author.name)
    for cdi in state.characters.get_all():
        if cdi.player_id is None and cdi.user == ctx.author.name:
            cdi.player_id = player.id
            state.characters.update_and_store(cdi)
    return player


def player_name(state: State, cdi: CharacterData) -> str:
    """Resolve the display name for a character's owner.

    Uses the PlayerData name when available, falls back to the legacy user string.
    """
    if cdi.player_id is not None:
        player = state.players.get_from_id(cdi.player_id)
        if player is not None:
            return player.name
    return cdi.user


async def send_in_parts(
    ctx: Context,
    parts: Iterable[str],
) -> None:
    msg: str = ""
    for txt in parts:
        if len(msg) + len(txt) >= 2000:
            await ctx.send(msg)
            msg = ""
        msg += "\n" + txt
    if msg:
        await ctx.send(msg)
