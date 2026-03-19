# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from initbot_chat.commands.augur import augurs, augur


async def test_augurs_lists_all(mock_ctx):
    await augurs.callback(mock_ctx)
    mock_ctx.send.assert_called()
    all_msgs = " ".join(str(call) for call in mock_ctx.send.call_args_list)
    assert "test" in all_msgs  # augur description is "test" in test data


async def test_augur_returns_one(mock_ctx):
    await augur.callback(mock_ctx)
    mock_ctx.send.assert_called_once()
