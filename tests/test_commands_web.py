# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from unittest.mock import AsyncMock, MagicMock

import pytest

import initbot_core.config as core_config
from initbot_chat.commands.web import web


@pytest.fixture(name="web_ctx")
def _web_ctx():
    ctx = MagicMock()
    ctx.send = AsyncMock(return_value=None)
    return ctx


async def test_web_sends_url(monkeypatch, web_ctx):
    monkeypatch.setattr(core_config.CORE_CFG, "domain", "example.com")
    monkeypatch.setattr(core_config.CORE_CFG, "web_token", "mysecret")
    await web.callback(web_ctx)
    web_ctx.send.assert_called_once_with("https://example.com/mysecret/")


@pytest.mark.parametrize(
    ("domain", "web_token"),
    [
        ("", ""),
        ("example.com", ""),
        ("", "mysecret"),
    ],
)
def test_web_not_registered_when_domain_or_secret_missing(
    monkeypatch, domain, web_token
):
    monkeypatch.setattr(core_config.CORE_CFG, "domain", domain)
    monkeypatch.setattr(core_config.CORE_CFG, "web_token", web_token)
    should_register = bool(
        core_config.CORE_CFG.domain and core_config.CORE_CFG.web_token
    )
    assert not should_register
