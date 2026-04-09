# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import shutil
from unittest.mock import AsyncMock, MagicMock

import pytest

import initbot_core.config as core_config
from initbot_chat.commands.web import web
from initbot_core.state.factory import create_state_from_source
from tests.helpers import DATA_DIR, REFERENCE_FILES


@pytest.fixture(name="sqlite_state")
def _sqlite_state(tmp_path):
    db_path = tmp_path / "test.db"
    state = create_state_from_source(f"sqlite:{db_path}")
    ref_dir = tmp_path / "ref"
    ref_dir.mkdir()
    for f in REFERENCE_FILES:
        shutil.copy(DATA_DIR / f, ref_dir / f)
    state.import_from(create_state_from_source(f"json:{ref_dir}"))
    return state


@pytest.fixture(name="web_ctx")
def _web_ctx(sqlite_state):
    ctx = MagicMock()
    ctx.author.id = 100000000000000001
    ctx.author.name = "testuser"
    ctx.author.display_name = "testuser"
    ctx.author.send = AsyncMock(return_value=None)
    ctx.send = AsyncMock(return_value=None)
    ctx.guild = MagicMock()  # guild channel context
    ctx.bot.initbot_state = sqlite_state
    return ctx


@pytest.fixture(name="dm_ctx")
def _dm_ctx(sqlite_state):
    ctx = MagicMock()
    ctx.author.id = 100000000000000001
    ctx.author.name = "testuser"
    ctx.author.display_name = "testuser"
    ctx.author.send = AsyncMock(return_value=None)
    ctx.send = AsyncMock(return_value=None)
    ctx.guild = None  # DM context
    ctx.bot.initbot_state = sqlite_state
    return ctx


async def test_web_sends_dm_with_token(monkeypatch, web_ctx):
    monkeypatch.setattr(core_config.CORE_CFG, "domain", "example.com")
    monkeypatch.setattr(core_config.CORE_CFG, "web_url_path_prefix", "testprefix")
    await web.callback(web_ctx)
    web_ctx.author.send.assert_called_once()
    dm_text = web_ctx.author.send.call_args[0][0]
    assert "https://example.com/testprefix/" in dm_text
    assert "expires in 1 minute" in dm_text


async def test_web_sends_localhost_url_when_no_domain(monkeypatch, web_ctx):
    monkeypatch.setattr(core_config.CORE_CFG, "domain", "")
    monkeypatch.setattr(core_config.CORE_CFG, "web_url_path_prefix", "testprefix")
    await web.callback(web_ctx)
    dm_text = web_ctx.author.send.call_args[0][0]
    assert "http://localhost:8080/testprefix/" in dm_text


async def test_web_sends_channel_notification(monkeypatch, web_ctx):
    monkeypatch.setattr(core_config.CORE_CFG, "domain", "example.com")
    await web.callback(web_ctx)
    web_ctx.send.assert_called_once()
    channel_text = web_ctx.send.call_args[0][0]
    assert "DM" in channel_text
    # Channel message must auto-delete
    assert web_ctx.send.call_args.kwargs.get("delete_after") == 5


async def test_web_token_is_single_use(monkeypatch, web_ctx):
    monkeypatch.setattr(core_config.CORE_CFG, "domain", "example.com")
    await web.callback(web_ctx)
    first_dm = web_ctx.author.send.call_args[0][0]

    await web.callback(web_ctx)
    second_dm = web_ctx.author.send.call_args[0][0]

    # Each call creates a distinct token
    assert first_dm != second_dm


async def test_web_token_stored_in_state(monkeypatch, web_ctx):
    monkeypatch.setattr(core_config.CORE_CFG, "domain", "example.com")
    await web.callback(web_ctx)
    dm_text = web_ctx.author.send.call_args[0][0]
    # Extract token from URL: last path segment before trailing slash
    token = dm_text.split("/")[-2]
    result = web_ctx.bot.initbot_state.web_login_tokens.find_valid(token)
    assert result is not None


async def test_web_no_channel_notification_when_invoked_in_dm(monkeypatch, dm_ctx):
    monkeypatch.setattr(core_config.CORE_CFG, "domain", "example.com")
    await web.callback(dm_ctx)
    dm_ctx.author.send.assert_called_once()  # DM was sent
    dm_ctx.send.assert_not_called()  # no channel notification
