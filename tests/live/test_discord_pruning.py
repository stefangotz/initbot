# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import sys
import time
from unittest.mock import MagicMock, patch

import discord
import pytest

# bot.py's chat config uses _cli_parse_args=True, so importing it while pytest
# is running would cause pydantic-settings to try to parse pytest's argv as
# Discord bot settings and fail. Clear argv before the import and ensure a
# dummy token is set so the interactive getpass prompt is also skipped.
os.environ.setdefault("TOKEN", "_test_token_")
_argv = sys.argv[:]
sys.argv = sys.argv[:1]
# pylint: disable=wrong-import-position
from initbot_chat.bot import _send_pruning_notifications  # noqa: E402

sys.argv = _argv

from initbot_core.data.character import NewCharacterData  # noqa: E402

# pylint: enable=wrong-import-position

_GOTZMODE_DISCORD_ID = 689763522539945989
_GOTZMODES_GUILD_ID = 868111923592454195
_FUTURE = int(time.time()) + 200 * 86400


async def test_fetch_member_returns_gotzmode(live_bot: discord.Client) -> None:
    guild = discord.utils.get(live_bot.guilds, id=_GOTZMODES_GUILD_ID)
    assert guild is not None, f"Bot is not in guild {_GOTZMODES_GUILD_ID}"
    member = await guild.fetch_member(_GOTZMODE_DISCORD_ID)
    assert member.id == _GOTZMODE_DISCORD_ID
    assert member.name == "gotzmode"


async def test_pruning_notification_dm_sent_via_fetch_member(
    live_bot: discord.Client, caplog: pytest.LogCaptureFixture
) -> None:
    char = NewCharacterData(name="TestPruneChar", user="gotzmode")
    char.last_used = 0
    char.player_id = 1

    mock_player = MagicMock()
    mock_player.discord_id = _GOTZMODE_DISCORD_ID

    mock_state = MagicMock()
    mock_state.characters.get_all.return_value = [char]
    mock_state.players.get_from_id.return_value = mock_player

    with patch("initbot_core.data.character.time") as mock_t:
        mock_t.time.return_value = _FUTURE
        await _send_pruning_notifications(live_bot.guilds, mock_state)

    warnings = [r.message for r in caplog.records if r.levelname == "WARNING"]
    assert not any("Could not find guild member" in w for w in warnings)
    assert not any("Could not send pruning notification DM" in w for w in warnings)
