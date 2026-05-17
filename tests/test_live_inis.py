# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# pylint: disable=protected-access  # tests must access private module internals

import asyncio
import contextlib
import sys
import time
from unittest.mock import AsyncMock, MagicMock, patch

import discord

from initbot_chat.commands.character import prune, remove, rename, touch
from initbot_chat.commands.init import inis, init
from initbot_chat.commands.utils import (
    LiveInisRef,
    _refresh_for_guild,
    refresh_all_live_inis,
    refresh_live_inis,
)


def _make_msg_mock() -> MagicMock:
    msg = MagicMock()
    msg.id = 777000000000000001
    msg.edit = AsyncMock(return_value=None)
    return msg


def _live_ref(msg_mock: MagicMock, offset: int = 0) -> LiveInisRef:
    return LiveInisRef(message=msg_mock, posted_at=int(time.time()) - offset)


async def test_inis_stores_message_ref(mock_ctx):
    await inis.callback(mock_ctx)
    guild_id = mock_ctx.guild.id
    assert guild_id in mock_ctx.bot.last_inis_message
    ref = mock_ctx.bot.last_inis_message[guild_id]
    assert ref.message is mock_ctx.send.return_value
    assert abs(ref.posted_at - int(time.time())) <= 2


async def test_inis_overwrites_previous_ref(mock_ctx):
    await inis.callback(mock_ctx)
    first_ref = mock_ctx.bot.last_inis_message[mock_ctx.guild.id]
    await inis.callback(mock_ctx)
    second_ref = mock_ctx.bot.last_inis_message[mock_ctx.guild.id]
    assert second_ref is not first_ref


async def test_init_refreshes_live_embed(mock_ctx, initbot_state):
    mock_ctx.bot.initbot_state = initbot_state
    player = initbot_state.players.upsert_discord(
        discord_id=mock_ctx.author.id, name=mock_ctx.author.name
    )
    cdi = initbot_state.characters.get_from_tokens(
        ["Hero"], create=True, player_id=player.id
    )
    cdi.initiative_dice = "d20"
    initbot_state.characters.update_and_store(cdi)

    msg_mock = _make_msg_mock()
    mock_ctx.bot.last_inis_message[mock_ctx.guild.id] = _live_ref(msg_mock)

    await init.callback(mock_ctx)
    msg_mock.edit.assert_awaited_once()
    embed_arg = msg_mock.edit.call_args.kwargs["embed"]
    assert embed_arg.title == "Initiative Order"


async def test_remove_refreshes_live_embed(mock_ctx, initbot_state):
    mock_ctx.bot.initbot_state = initbot_state
    player = initbot_state.players.upsert_discord(
        discord_id=mock_ctx.author.id, name=mock_ctx.author.name
    )
    initbot_state.characters.get_from_tokens(["Hero"], create=True, player_id=player.id)

    msg_mock = _make_msg_mock()
    mock_ctx.bot.last_inis_message[mock_ctx.guild.id] = _live_ref(msg_mock)

    await remove.callback(mock_ctx, "Hero")
    msg_mock.edit.assert_awaited_once()


async def test_rename_refreshes_live_embed(mock_ctx, initbot_state):
    mock_ctx.bot.initbot_state = initbot_state
    player = initbot_state.players.upsert_discord(
        discord_id=mock_ctx.author.id, name=mock_ctx.author.name
    )
    initbot_state.characters.get_from_tokens(["Hero"], create=True, player_id=player.id)

    msg_mock = _make_msg_mock()
    mock_ctx.bot.last_inis_message[mock_ctx.guild.id] = _live_ref(msg_mock)

    await rename.callback(mock_ctx, "Hero", "Champion")
    msg_mock.edit.assert_awaited_once()


async def test_prune_refreshes_live_embed(mock_ctx, initbot_state):
    mock_ctx.bot.initbot_state = initbot_state
    player = initbot_state.players.upsert_discord(
        discord_id=mock_ctx.author.id, name=mock_ctx.author.name
    )
    cdi = initbot_state.characters.get_from_tokens(
        ["OldHero"], create=True, player_id=player.id
    )
    cdi.last_used = int(time.time()) - 200 * 24 * 3600
    initbot_state.characters.update_and_store(cdi)

    msg_mock = _make_msg_mock()
    mock_ctx.bot.last_inis_message[mock_ctx.guild.id] = _live_ref(msg_mock)

    await prune.callback(mock_ctx)
    msg_mock.edit.assert_awaited_once()


async def test_prune_no_refresh_when_nothing_pruned(mock_ctx, initbot_state):
    mock_ctx.bot.initbot_state = initbot_state
    initbot_state.players.upsert_discord(
        discord_id=mock_ctx.author.id, name=mock_ctx.author.name
    )

    msg_mock = _make_msg_mock()
    mock_ctx.bot.last_inis_message[mock_ctx.guild.id] = _live_ref(msg_mock)

    await prune.callback(mock_ctx)
    msg_mock.edit.assert_not_awaited()


async def test_touch_refreshes_live_embed(mock_ctx, initbot_state):
    mock_ctx.bot.initbot_state = initbot_state
    player = initbot_state.players.upsert_discord(
        discord_id=mock_ctx.author.id, name=mock_ctx.author.name
    )
    initbot_state.characters.get_from_tokens(["Hero"], create=True, player_id=player.id)

    msg_mock = _make_msg_mock()
    mock_ctx.bot.last_inis_message[mock_ctx.guild.id] = _live_ref(msg_mock)

    await touch.callback(mock_ctx)
    msg_mock.edit.assert_awaited_once()


async def test_refresh_skips_expired_ref(mock_ctx):
    guild_id = mock_ctx.guild.id
    msg_mock = _make_msg_mock()
    mock_ctx.bot.last_inis_message[guild_id] = _live_ref(msg_mock, offset=28801)

    await _refresh_for_guild(mock_ctx.bot, guild_id)

    msg_mock.edit.assert_not_awaited()
    assert guild_id not in mock_ctx.bot.last_inis_message


async def test_refresh_clears_on_not_found(mock_ctx):
    guild_id = mock_ctx.guild.id
    msg_mock = _make_msg_mock()
    msg_mock.edit = AsyncMock(
        side_effect=discord.NotFound(MagicMock(status=404), "not found")
    )
    mock_ctx.bot.last_inis_message[guild_id] = _live_ref(msg_mock)

    await _refresh_for_guild(mock_ctx.bot, guild_id)

    assert guild_id not in mock_ctx.bot.last_inis_message


async def test_refresh_keeps_ref_on_http_exception(mock_ctx):
    guild_id = mock_ctx.guild.id
    msg_mock = _make_msg_mock()
    msg_mock.edit = AsyncMock(
        side_effect=discord.HTTPException(MagicMock(status=500), "server error")
    )
    mock_ctx.bot.last_inis_message[guild_id] = _live_ref(msg_mock)

    await _refresh_for_guild(mock_ctx.bot, guild_id)

    assert guild_id in mock_ctx.bot.last_inis_message


async def test_refresh_works_in_dm(mock_ctx, initbot_state):
    """DM channels have no guild; the channel ID is used as the key instead."""
    mock_ctx.bot.initbot_state = initbot_state
    mock_ctx.guild = None
    dm_channel_id = mock_ctx.channel.id

    msg_mock = _make_msg_mock()
    mock_ctx.bot.last_inis_message[dm_channel_id] = _live_ref(msg_mock)

    await refresh_live_inis(mock_ctx)
    msg_mock.edit.assert_awaited_once()


async def test_inis_stores_ref_in_dm(mock_ctx):
    """$inis in a DM stores the ref keyed on channel ID, not guild ID."""
    mock_ctx.guild = None
    await inis.callback(mock_ctx)
    assert mock_ctx.channel.id in mock_ctx.bot.last_inis_message


async def test_refresh_all_guilds(mock_ctx, initbot_state):
    mock_ctx.bot.initbot_state = initbot_state

    msg_a = _make_msg_mock()
    msg_b = _make_msg_mock()
    mock_ctx.bot.last_inis_message[111000000000000001] = _live_ref(msg_a)
    mock_ctx.bot.last_inis_message[222000000000000002] = _live_ref(msg_b)

    await refresh_all_live_inis(mock_ctx.bot)

    msg_a.edit.assert_awaited_once()
    msg_b.edit.assert_awaited_once()


async def test_datagram_triggers_refresh():
    bot_module = sys.modules["initbot_chat.bot"]
    protocol = bot_module._BotUdpProtocol()

    loop = asyncio.get_running_loop()
    created_tasks = []
    original_create_task = loop.create_task

    def _capture_task(coro, **kwargs):
        task = original_create_task(coro, **kwargs)
        created_tasks.append(task)
        return task

    with patch.object(loop, "create_task", side_effect=_capture_task):
        protocol.datagram_received(b"", ("127.0.0.1", 9877))

    assert len(created_tasks) == 1
    created_tasks[0].cancel()
    with contextlib.suppress(asyncio.CancelledError, Exception):
        await created_tasks[0]
