# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from initbot_chat.commands.crit import crit


async def test_crit_returns_effect(mock_ctx):
    # Test data has crit table 1, roll 1 with effect "test"
    await crit.callback(mock_ctx, 1, 1)
    mock_ctx.send.assert_called_once()
    assert mock_ctx.send.call_args[0][0] == "test"
