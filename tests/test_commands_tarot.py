# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from unittest.mock import AsyncMock, MagicMock

import pytest

from initbot_chat.commands.tarot import tarot


@pytest.fixture(name="tarot_ctx")
def _tarot_ctx():
    ctx = MagicMock()
    ctx.send = AsyncMock(return_value=None)
    return ctx


async def test_tarot_sends_url(tarot_ctx):
    await tarot.callback(tarot_ctx)
    tarot_ctx.send.assert_called_once()
    url = tarot_ctx.send.call_args[0][0]
    assert url.startswith("https://randomtarotcard.com/")
    assert url.endswith(".jpg")
