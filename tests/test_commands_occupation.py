# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from initbot_chat.commands.occupation import occupations


async def test_occupations_lists_all(mock_ctx):
    await occupations.callback(mock_ctx)
    mock_ctx.send.assert_called()
    all_msgs = " ".join(str(call) for call in mock_ctx.send.call_args_list)
    # Test data has a single occupation with name, weapon, and goods all set to "test"
    assert "test" in all_msgs
