# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from unittest.mock import AsyncMock, MagicMock

import pytest

from initbot_chat.commands.levels import levels


@pytest.fixture(name="levels_ctx")
def _levels_ctx():
    ctx = MagicMock()
    ctx.send = AsyncMock(return_value=None)
    return ctx


async def test_levels_sends_xp_table(levels_ctx):
    await levels.callback(levels_ctx)
    levels_ctx.send.assert_called_once()
    msg = levels_ctx.send.call_args[0][0]
    assert "Level 0: 0 XP" in msg
    assert "Level 1: 10 XP" in msg
    assert "Level 10: 1090 XP" in msg
