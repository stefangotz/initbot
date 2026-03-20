# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from initbot_chat.commands.cls import classes, cls


async def test_classes_lists_names(mock_ctx):
    await classes.callback(mock_ctx)
    mock_ctx.send.assert_called_once()
    msg = str(mock_ctx.send.call_args[0][0])
    # Test data has a single class named "test"
    assert "test" in msg


async def test_cls_shows_details(mock_ctx):
    await cls.callback(mock_ctx, "test")
    mock_ctx.send.assert_called_once()
