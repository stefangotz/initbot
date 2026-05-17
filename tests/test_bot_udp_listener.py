# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# pylint: disable=protected-access  # tests must access private module internals

import asyncio
import contextlib
import logging
import socket
import sys
from unittest.mock import AsyncMock, MagicMock, patch


def _free_udp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _bot():
    """Return the live module object so tests always patch the right namespace."""
    return sys.modules["initbot_chat.bot"]


async def test_setup_hook_starts_listener(monkeypatch):
    bot = _bot()
    port = _free_udp_port()
    monkeypatch.setattr(bot.CFG, "chat_notify_host", "127.0.0.1")
    monkeypatch.setattr(bot.CFG, "chat_notify_port", port)
    bot._udp_transport = None
    try:
        await bot._setup_hook()
        assert bot._udp_transport is not None
    finally:
        if bot._udp_transport is not None:
            bot._udp_transport.close()
        bot._udp_transport = None


async def test_setup_hook_is_idempotent(monkeypatch):
    bot = _bot()
    port = _free_udp_port()
    monkeypatch.setattr(bot.CFG, "chat_notify_host", "127.0.0.1")
    monkeypatch.setattr(bot.CFG, "chat_notify_port", port)
    mock_transport = MagicMock()
    bot._udp_transport = mock_transport
    try:
        await bot._setup_hook()
        assert bot._udp_transport is mock_transport
    finally:
        bot._udp_transport = None


async def test_close_closes_transport(monkeypatch):
    bot = _bot()
    mock_transport = MagicMock()
    bot._udp_transport = mock_transport
    mock_original = AsyncMock()
    monkeypatch.setattr(bot, "_original_bot_close", mock_original)
    await bot._bot_close()
    mock_transport.close.assert_called_once()
    assert bot._udp_transport is None
    mock_original.assert_awaited_once()


async def test_close_without_transport_does_not_raise(monkeypatch):
    bot = _bot()
    bot._udp_transport = None
    mock_original = AsyncMock()
    monkeypatch.setattr(bot, "_original_bot_close", mock_original)
    await bot._bot_close()
    mock_original.assert_awaited_once()


async def test_protocol_logs_on_receipt(caplog):
    bot_module = _bot()
    protocol = bot_module._BotUdpProtocol()
    loop = asyncio.get_running_loop()
    created_tasks = []
    original_create_task = loop.create_task

    def _capture(coro, **kwargs):
        task = original_create_task(coro, **kwargs)
        created_tasks.append(task)
        return task

    with (
        patch.object(loop, "create_task", side_effect=_capture),
        caplog.at_level(logging.DEBUG, logger="initbot_chat.bot"),
    ):
        protocol.datagram_received(b"", ("127.0.0.1", 9877))

    assert "External state change notification" in caplog.text
    for task in created_tasks:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError, Exception):
            await task
