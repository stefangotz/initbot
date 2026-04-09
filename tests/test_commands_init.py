# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import time

from discord.ext import commands

from initbot_chat.commands.init import inis, init, init_error
from initbot_core.data.character import NewCharacterData


async def test_init_explicit_value(mock_ctx):
    mock_ctx.bot.initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Mel", player_id=mock_ctx.author.player_id)
    )
    await init.callback(mock_ctx, "Mel", "10")
    mock_ctx.send.assert_called_once()
    msg = mock_ctx.send.call_args[0][0]
    assert "10" in msg
    mel = mock_ctx.bot.initbot_state.characters.get_from_name("Mel")
    assert mel.initiative == 10


async def test_init_value_first(mock_ctx):
    mock_ctx.bot.initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Mel", player_id=mock_ctx.author.player_id)
    )
    await init.callback(mock_ctx, "10", "Mel")
    mel = mock_ctx.bot.initbot_state.characters.get_from_name("Mel")
    assert mel.initiative == 10


async def test_init_auto_roll(mock_ctx):
    mock_ctx.bot.initbot_state.characters.add_store_and_get(
        NewCharacterData(
            name="Mel",
            player_id=mock_ctx.author.player_id,
            initiative_dice="d20+3",
        )
    )
    await init.callback(mock_ctx)
    mel = mock_ctx.bot.initbot_state.characters.get_from_name("Mel")
    assert isinstance(mel.initiative, int)
    assert 4 <= mel.initiative <= 23


async def test_init_auto_roll_no_dice(mock_ctx):
    mock_ctx.bot.initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Mel", player_id=mock_ctx.author.player_id)
    )
    try:
        await init.callback(mock_ctx)
    except ValueError as exc:
        await init_error(mock_ctx, commands.CommandError(str(exc)))  # type: ignore[missing-argument]  # discord.py stubs type error handlers as (self, ctx, error) | (ctx, error)
    mock_ctx.send.assert_called()


async def test_init_ci_name_finds_existing_character(mock_ctx):
    """$init with a case-variant name finds the existing character rather than creating one."""
    mock_ctx.bot.initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Foo", player_id=mock_ctx.author.player_id)
    )
    await init.callback(mock_ctx, "foo", "7")
    char = mock_ctx.bot.initbot_state.characters.get_from_name("Foo")
    assert char.initiative == 7
    assert len(mock_ctx.bot.initbot_state.characters.get_all()) == 1


async def test_inis_shows_initiative_order(mock_ctx):
    now = int(time.time())
    pid = mock_ctx.author.player_id
    alpha = NewCharacterData(name="Alpha", player_id=pid, initiative=10, last_used=now)
    beta = NewCharacterData(name="Beta", player_id=pid, initiative=5, last_used=now)
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
    # last_used set far in the past → should be filtered out
    old_time = int(time.time()) - 25 * 3600
    old = NewCharacterData(
        name="Old",
        player_id=mock_ctx.author.player_id,
        initiative=15,
        last_used=old_time,
    )
    mock_ctx.bot.initbot_state.characters.add_store_and_get(old)

    await inis.callback(mock_ctx)
    mock_ctx.send.assert_called_once()

    embed = mock_ctx.send.call_args.kwargs["embed"]
    assert "Old" not in (embed.description or "")


async def test_inis_excludes_characters_without_initiative(mock_ctx):
    now = int(time.time())
    no_init = NewCharacterData(
        name="NoInit",
        player_id=mock_ctx.author.player_id,
        last_used=now,
    )
    mock_ctx.bot.initbot_state.characters.add_store_and_get(no_init)

    await inis.callback(mock_ctx)
    mock_ctx.send.assert_called_once()

    embed = mock_ctx.send.call_args.kwargs["embed"]
    assert "NoInit" not in (embed.description or "")
