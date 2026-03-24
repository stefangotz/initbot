# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from collections.abc import Iterable

from discord.ext.commands import Context

from initbot_core.data.character import CharacterData
from initbot_core.data.player import PlayerData
from initbot_core.state.state import State


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
