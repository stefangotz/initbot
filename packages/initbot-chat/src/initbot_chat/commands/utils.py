# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Final, Protocol

import discord
from discord import Embed, Message
from discord.ext import commands
from discord.ext.commands import Context

from initbot_core.config import CORE_CFG
from initbot_core.data.character import CharacterData
from initbot_core.data.player import PlayerData
from initbot_core.state.state import State

_log = logging.getLogger(__name__)

_LIVE_INIS_TTL_SECONDS: Final[int] = 28800  # 8 hours


@dataclass
class LiveInisRef:
    message: Message
    posted_at: int


class _BotProtocol(Protocol):
    last_inis_message: dict[int, LiveInisRef]
    initbot_state: State


def _web_configured(_ctx: commands.Context) -> bool:
    if not (CORE_CFG.web_hostname and CORE_CFG.web_url_path_prefix):
        raise commands.CheckFailure(
            "The web command is not available (WEB_HOSTNAME or WEB_URL_PATH_PREFIX not configured)."
        )
    return True


web_configured: Final[Callable[..., Any]] = commands.check(_web_configured)


def sync_player(state: State, ctx: Context) -> PlayerData:
    """Upsert the player record for the Discord user."""
    return state.players.upsert_discord(discord_id=ctx.author.id, name=ctx.author.name)


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


def build_inis_embed(state: State) -> Embed:
    """Build the initiative-order embed from current state."""

    def has_recent_initiative(cdi: CharacterData) -> bool:
        return (
            cdi.initiative is not None
            and cdi.last_used is not None
            and cdi.last_used > int(datetime.now().timestamp()) - 24 * 3600
        )

    sorted_characters = sorted(
        filter(has_recent_initiative, state.characters.get_all()),
        key=lambda c: c.initiative or 0,
        reverse=True,
    )
    players_by_id = {p.id: p for p in state.players.get_all()}
    desc: str = "\n".join(
        f"{cdi.initiative}: **{cdi.name}** (*{players_by_id[cdi.player_id].name}*)"
        for cdi in sorted_characters
    )
    return Embed(title="Initiative Order", description=desc)


async def _refresh_for_guild(bot: _BotProtocol, guild_id: int) -> None:
    ref: LiveInisRef | None = bot.last_inis_message.get(guild_id)
    if ref is None or time.time() - ref.posted_at >= _LIVE_INIS_TTL_SECONDS:
        bot.last_inis_message.pop(guild_id, None)
        return
    try:
        await ref.message.edit(embed=build_inis_embed(bot.initbot_state))
        _log.debug("Live inis embed updated for guild %d", guild_id)
    except discord.NotFound:
        _log.warning("Live inis message %d not found; clearing ref", ref.message.id)
        bot.last_inis_message.pop(guild_id, None)
    except discord.HTTPException:
        _log.warning(
            "HTTP error refreshing live inis for guild %d; will retry", guild_id
        )


def _live_inis_key(ctx: Context) -> int:
    """Return the key used to store/retrieve the live $inis ref for this context."""
    return ctx.guild.id if ctx.guild is not None else ctx.channel.id  # type: ignore[return-value]


async def refresh_live_inis(ctx: Context) -> None:
    """Refresh the live $inis embed after a bot command changes initiative state."""
    await _refresh_for_guild(ctx.bot, _live_inis_key(ctx))  # type: ignore[arg-type]


async def refresh_all_live_inis(bot: _BotProtocol) -> None:
    """Refresh live $inis embeds for all guilds; called via UDP notification from web app."""
    for guild_id in list(bot.last_inis_message.keys()):
        await _refresh_for_guild(bot, guild_id)
