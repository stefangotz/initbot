# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

from initbot_core.state.factory import create_state_from_source

# initbot_chat.bot imports a Settings object at module level with _cli_parse_args=True.
# Importing it while pytest is running would cause pydantic-settings to parse pytest's
# argv as bot settings. Clear argv first and ensure a dummy token suppresses the
# interactive getpass prompt. This runs before any test module is loaded, so the
# subsequent imports in bot test files are no-ops against sys.modules.
os.environ.setdefault("TOKEN", "_test_token_")
_argv = sys.argv[:]
sys.argv = sys.argv[:1]
import initbot_chat.bot  # noqa: E402, F401  # pylint: disable=wrong-import-position,unused-import

sys.argv = _argv


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
    player = initbot_state.players.upsert_discord(discord_id=discord_id, name=name)
    ctx.author.player_id = player.id  # pylint: disable=no-member
    ctx.bot.initbot_state = initbot_state
    ctx.send = AsyncMock(return_value=None)
    return ctx
