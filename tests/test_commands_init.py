# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import time

from discord.ext import commands

from initbot_chat.commands.init import inis, init, init_error
from initbot_core.data.character import NewCharacterData
from initbot_core.models.character import Character


async def test_init_explicit_value(mock_ctx):
    mock_ctx.bot.initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Mel", user="testuser")
    )
    await init.callback(mock_ctx, "Mel", "10")
    mock_ctx.send.assert_called_once()
    msg = mock_ctx.send.call_args[0][0]
    assert "10" in msg
    mel = mock_ctx.bot.initbot_state.characters.get_from_name("Mel")
    assert mel.initiative == 10


async def test_init_value_first(mock_ctx):
    mock_ctx.bot.initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Mel", user="testuser")
    )
    await init.callback(mock_ctx, "10", "Mel")
    mel = mock_ctx.bot.initbot_state.characters.get_from_name("Mel")
    assert mel.initiative == 10


async def test_init_auto_roll(mock_ctx):
    mock_ctx.bot.initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Mel", user="testuser", agility=14)
    )
    await init.callback(mock_ctx)
    mel = mock_ctx.bot.initbot_state.characters.get_from_name("Mel")
    modifier = Character(mel, mock_ctx.bot.initbot_state).initiative_modifier
    assert modifier is not None
    assert isinstance(mel.initiative, int)
    assert 1 + modifier <= mel.initiative <= 20 + modifier


async def test_init_auto_roll_no_agility(mock_ctx):
    mock_ctx.bot.initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Mel", user="testuser")
    )
    try:
        await init.callback(mock_ctx)
    except ValueError as exc:
        await init_error(mock_ctx, commands.CommandError(str(exc)))  # type: ignore[missing-argument]  # discord.py stubs type error handlers as (self, ctx, error) | (ctx, error)
    mock_ctx.send.assert_called()


async def test_inis_shows_initiative_order(mock_ctx):
    now = int(time.time())
    alpha = NewCharacterData(
        name="Alpha", user="testuser", initiative=10, initiative_time=now
    )
    beta = NewCharacterData(
        name="Beta", user="testuser", initiative=5, initiative_time=now
    )
    mock_ctx.bot.initbot_state.characters.add_store_and_get(alpha)
    mock_ctx.bot.initbot_state.characters.add_store_and_get(beta)

    await inis.callback(mock_ctx)
    mock_ctx.send.assert_called_once()

    embed = mock_ctx.send.call_args.kwargs["embed"]
    desc = embed.description
    assert "Alpha" in desc
    assert "Beta" in desc
    assert desc.index("Alpha") < desc.index("Beta")


async def test_inis_filters_old_initiative(mock_ctx):
    # initiative_time set far in the past → should be filtered out
    old_time = int(time.time()) - 25 * 3600
    old = NewCharacterData(
        name="Old", user="testuser", initiative=15, initiative_time=old_time
    )
    mock_ctx.bot.initbot_state.characters.add_store_and_get(old)

    await inis.callback(mock_ctx)
    mock_ctx.send.assert_called_once()

    embed = mock_ctx.send.call_args.kwargs["embed"]
    assert "Old" not in (embed.description or "")


async def test_inis_excludes_parked_characters(mock_ctx):
    now = int(time.time())
    parked = NewCharacterData(
        name="Parked", user="testuser", initiative=20, initiative_time=now, active=False
    )
    mock_ctx.bot.initbot_state.characters.add_store_and_get(parked)

    await inis.callback(mock_ctx)
    mock_ctx.send.assert_called_once()

    embed = mock_ctx.send.call_args.kwargs["embed"]
    assert "Parked" not in (embed.description or "")
