import re

import pytest
from unittest.mock import AsyncMock, MagicMock

from initbot.bot.commands.roll import roll


@pytest.fixture
def roll_ctx():
    ctx = MagicMock()
    ctx.author.display_name = "testuser"
    ctx.send = AsyncMock(return_value=None)
    return ctx


async def test_roll_single_die(roll_ctx):
    await roll.callback(roll_ctx, "d6")
    roll_ctx.send.assert_called_once()
    msg = roll_ctx.send.call_args[0][0]
    assert re.search(r"testuser rolled \d+", msg)


async def test_roll_multiple_words(roll_ctx):
    await roll.callback(roll_ctx, "d20+5", "to", "attack")
    roll_ctx.send.assert_called_once()
    msg = roll_ctx.send.call_args[0][0]
    assert "to" in msg
    assert "attack" in msg
    assert re.search(r"\d+", msg)
