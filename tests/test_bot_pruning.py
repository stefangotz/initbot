# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import sys
import time
from unittest.mock import AsyncMock, MagicMock, patch

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
from initbot_chat.bot import (  # noqa: E402
    _send_pruning_notifications,
)

sys.argv = _argv

from initbot_core.data.character import NewCharacterData  # noqa: E402

# pylint: enable=wrong-import-position

_FUTURE = int(time.time()) + 200 * 86400
_PLAYER_ID = 42
_DISCORD_ID = 999888777


def _old_char(name: str, player_id: int = _PLAYER_ID) -> NewCharacterData:
    cdi = NewCharacterData(name=name, player_id=player_id)
    cdi.last_used = 0
    return cdi


def _recent_char(name: str) -> NewCharacterData:
    cdi = NewCharacterData(name=name, player_id=_PLAYER_ID)
    cdi.last_used = int(time.time())
    return cdi


def _mock_state_with_player(
    *chars: NewCharacterData, discord_id: int = _DISCORD_ID
) -> MagicMock:
    mock_player = MagicMock()
    mock_player.discord_id = discord_id
    mock_state = MagicMock()
    mock_state.characters.get_all.return_value = list(chars)
    mock_state.players.get_from_id.return_value = mock_player
    return mock_state


async def test_pruning_notification_sends_dm() -> None:
    char1 = _old_char("OldMel")
    char2 = _old_char("OldBob")
    mock_state = _mock_state_with_player(char1, char2)

    member = MagicMock()
    member.send = AsyncMock()

    guild = MagicMock()
    guild.fetch_member = AsyncMock(return_value=member)

    with patch("initbot_core.data.character.time") as mock_t:
        mock_t.time.return_value = _FUTURE
        await _send_pruning_notifications([guild], mock_state)

    member.send.assert_awaited_once()
    call_text = member.send.call_args[0][0]
    assert "OldMel" in call_text
    assert "OldBob" in call_text
    assert "$prune" in call_text


async def test_pruning_notification_member_not_found(
    caplog: pytest.LogCaptureFixture,
) -> None:
    char1 = _old_char("OldMel")
    mock_state = _mock_state_with_player(char1)

    mock_response = MagicMock()
    mock_response.status = 404

    guild = MagicMock()
    guild.fetch_member = AsyncMock(
        side_effect=discord.NotFound(mock_response, "Unknown Member")
    )

    with patch("initbot_core.data.character.time") as mock_t:
        mock_t.time.return_value = _FUTURE
        await _send_pruning_notifications([guild], mock_state)

    assert any(
        f"player_id={_PLAYER_ID}" in r.message
        for r in caplog.records
        if r.levelname == "WARNING"
    )


async def test_pruning_notification_dm_blocked(
    caplog: pytest.LogCaptureFixture,
) -> None:
    char1 = _old_char("OldMel")
    mock_state = _mock_state_with_player(char1)

    member = MagicMock()
    member.send = AsyncMock(side_effect=Exception("DMs blocked"))

    guild = MagicMock()
    guild.fetch_member = AsyncMock(return_value=member)

    with patch("initbot_core.data.character.time") as mock_t:
        mock_t.time.return_value = _FUTURE
        await _send_pruning_notifications([guild], mock_state)

    assert any(
        f"player_id={_PLAYER_ID}" in r.message
        for r in caplog.records
        if r.levelname == "WARNING"
    )


async def test_pruning_notification_uses_discord_id() -> None:
    char = _old_char("OldMel")
    mock_state = _mock_state_with_player(char, discord_id=_DISCORD_ID)

    member = MagicMock()
    member.send = AsyncMock()

    guild = MagicMock()
    guild.fetch_member = AsyncMock(return_value=member)

    with patch("initbot_core.data.character.time") as mock_t:
        mock_t.time.return_value = _FUTURE
        await _send_pruning_notifications([guild], mock_state)

    guild.fetch_member.assert_awaited_with(_DISCORD_ID)
    member.send.assert_awaited_once()


async def test_pruning_notification_player_not_in_guild(
    caplog: pytest.LogCaptureFixture,
) -> None:
    char = _old_char("OldMel")
    mock_state = _mock_state_with_player(char)

    mock_response = MagicMock()
    mock_response.status = 404

    guild = MagicMock()
    guild.fetch_member = AsyncMock(
        side_effect=discord.NotFound(mock_response, "Unknown Member")
    )

    with patch("initbot_core.data.character.time") as mock_t:
        mock_t.time.return_value = _FUTURE
        await _send_pruning_notifications([guild], mock_state)

    assert any(
        f"player_id={_PLAYER_ID}" in r.message
        for r in caplog.records
        if r.levelname == "WARNING"
    )


async def test_pruning_notification_skips_recent() -> None:
    char1 = _recent_char("RecentMel")

    mock_state = MagicMock()
    mock_state.characters.get_all.return_value = [char1]

    member = MagicMock()
    member.send = AsyncMock()

    guild = MagicMock()
    guild.fetch_member = AsyncMock(return_value=member)

    await _send_pruning_notifications([guild], mock_state)

    member.send.assert_not_awaited()
