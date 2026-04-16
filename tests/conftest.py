# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from unittest.mock import AsyncMock, MagicMock

import pytest

from initbot_core.state.factory import create_state_from_source


@pytest.fixture(name="initbot_state")
def _initbot_state(tmp_path):
    return create_state_from_source(f"sqlite:{tmp_path / 'test.db'}")


@pytest.fixture(name="mock_ctx")
def _mock_ctx(initbot_state):
    discord_id = 100000000000000001
    name = "testuser"
    ctx = MagicMock()
    ctx.author.id = discord_id
    ctx.author.name = name
    ctx.author.display_name = name
    player = initbot_state.players.upsert(discord_id=discord_id, name=name)
    ctx.author.player_id = player.id  # pylint: disable=no-member
    ctx.bot.initbot_state = initbot_state
    ctx.send = AsyncMock(return_value=None)
    return ctx
