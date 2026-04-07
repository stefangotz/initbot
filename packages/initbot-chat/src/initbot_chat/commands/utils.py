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


def _web_configured(_ctx: commands.Context) -> bool:
    if not (CORE_CFG.domain and CORE_CFG.web_url_path_prefix):
        raise commands.CheckFailure(
            "The web command is not available (DOMAIN or WEB_URL_PATH_PREFIX not configured)."
        )
    return True


web_configured: Final[Callable[..., Any]] = commands.check(_web_configured)


def sync_player(state: State, ctx: Context) -> PlayerData:
    """Upsert the player record for the Discord user."""
    return state.players.upsert(discord_id=ctx.author.id, name=ctx.author.name)


def player_name(state: State, cdi: CharacterData) -> str:
    """Resolve the display name for a character's owner via the player entity."""
    return state.players.get_from_id(cdi.player_id).name


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
