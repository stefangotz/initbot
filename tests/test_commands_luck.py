# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from unittest.mock import patch

from discord.ext import commands

from initbot_chat.commands.luck import handle_error, luck
from initbot_core.data.character import NewCharacterData


async def test_luck_no_luck_attribute(mock_ctx):
    mock_ctx.bot.initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Mel", user="testuser", luck=None)
    )
    try:
        await luck.callback(mock_ctx, "Mel")
    except ValueError as exc:
        await handle_error(mock_ctx, commands.CommandError(str(exc)))  # type: ignore[missing-argument]  # discord.py stubs type error handlers as (self, ctx, error) | (ctx, error)
    mock_ctx.send.assert_called()
    msg = mock_ctx.send.call_args[0][0]
    # Validates the f-string fix: character name must appear in the error message
    assert "Mel" in msg


async def test_luck_guaranteed_pass(mock_ctx):
    mock_ctx.bot.initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Mel", user="testuser", luck=18)
    )
    with patch("initbot_core.models.roll.NerdDiceRoll.roll_one", return_value=10):
        await luck.callback(mock_ctx, "Mel")
    mock_ctx.send.assert_called_once()
    msg = mock_ctx.send.call_args[0][0]
    assert "passed" in msg
    assert "8 under" in msg  # |10 - 18| = 8


async def test_luck_guaranteed_fail(mock_ctx):
    mock_ctx.bot.initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Mel", user="testuser", luck=5)
    )
    with patch("initbot_core.models.roll.NerdDiceRoll.roll_one", return_value=15):
        await luck.callback(mock_ctx, "Mel")
    mock_ctx.send.assert_called_once()
    msg = mock_ctx.send.call_args[0][0]
    assert "failed" in msg
    assert "10 over" in msg  # |15 - 5| = 10


async def test_luck_custom_die(mock_ctx):
    mock_ctx.bot.initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Mel", user="testuser", luck=18)
    )
    with patch("initbot_core.models.roll.NerdDiceRoll.roll_one", return_value=3):
        await luck.callback(mock_ctx, "Mel", "d6")
    mock_ctx.send.assert_called_once()
