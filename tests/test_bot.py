# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import sys
import types
from unittest.mock import AsyncMock, MagicMock, patch


def _make_cfg(max_length=90):
    cfg = MagicMock()
    cfg.command_prefixes = "$"
    cfg.max_inline_roll_message_length = max_length
    return cfg


def _make_message(content):
    msg = MagicMock()
    msg.content = content
    # Ensure the bot's self-message check fails (author != bot.user)
    msg.author = object()
    msg.channel.send = AsyncMock(return_value=None)
    return msg


def _make_bot_module(cfg):
    """Import initbot_chat.bot with a pre-injected mock config."""
    fake_config_mod = types.ModuleType("initbot_chat.config")
    fake_config_mod.CFG = cfg  # type: ignore[attr-defined]

    saved = sys.modules.pop("initbot_chat.bot", None)
    sys.modules["initbot_chat.config"] = fake_config_mod
    try:
        import initbot_chat.bot as bot_mod  # pylint: disable=import-outside-toplevel

        return bot_mod
    finally:
        # Restore original state so other tests aren't affected
        sys.modules.pop("initbot_chat.bot", None)
        sys.modules.pop("initbot_chat.config", None)
        if saved is not None:
            sys.modules["initbot_chat.bot"] = saved


async def test_short_message_with_dice_roll_is_expanded():
    cfg = _make_cfg(max_length=90)
    bot_mod = _make_bot_module(cfg)

    msg = _make_message("Roll d6")
    with patch.object(bot_mod, "CFG", cfg):
        await bot_mod.on_message(msg)
    msg.channel.send.assert_called_once()
    sent = msg.channel.send.call_args[0][0]
    assert sent != "Roll d6"


async def test_long_message_with_dice_roll_is_not_expanded():
    cfg = _make_cfg(max_length=90)
    bot_mod = _make_bot_module(cfg)

    long_msg = (
        "This is a very long non-game message that happens to mention d20 in passing "
        + "x" * 20
    )
    assert len(long_msg) > 90
    msg = _make_message(long_msg)
    with patch.object(bot_mod, "CFG", cfg):
        await bot_mod.on_message(msg)
    msg.channel.send.assert_not_called()


async def test_message_exactly_at_limit_is_expanded():
    cfg = _make_cfg(max_length=90)
    bot_mod = _make_bot_module(cfg)

    prefix = "Roll d6 "
    padding = "x" * (90 - len(prefix))
    content = prefix + padding
    assert len(content) == 90
    msg = _make_message(content)
    with patch.object(bot_mod, "CFG", cfg):
        await bot_mod.on_message(msg)
    msg.channel.send.assert_called_once()
    sent = msg.channel.send.call_args[0][0]
    assert sent != content


async def test_message_one_over_limit_is_not_expanded():
    cfg = _make_cfg(max_length=90)
    bot_mod = _make_bot_module(cfg)

    prefix = "Roll d6 "
    padding = "x" * (91 - len(prefix))
    content = prefix + padding
    assert len(content) == 91
    msg = _make_message(content)
    with patch.object(bot_mod, "CFG", cfg):
        await bot_mod.on_message(msg)
    msg.channel.send.assert_not_called()


async def test_custom_limit_is_respected():
    cfg = _make_cfg(max_length=20)
    bot_mod = _make_bot_module(cfg)

    content = "Roll d6 with extras padding here exceeding 20"
    assert len(content) > 20
    msg = _make_message(content)
    with patch.object(bot_mod, "CFG", cfg):
        await bot_mod.on_message(msg)
    msg.channel.send.assert_not_called()
