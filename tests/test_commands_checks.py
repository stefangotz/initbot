# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from unittest.mock import MagicMock

import pytest
from discord.ext.commands import CheckFailure

import initbot_core.config as core_config
from initbot_chat.commands.utils import web_configured
from tests.helpers import predicate_from


@pytest.mark.parametrize(
    ("domain", "prefix"),
    [("", ""), ("example.com", ""), ("", "secret")],
)
def test_web_configured_raises_when_missing(monkeypatch, domain, prefix):
    monkeypatch.setattr(core_config.CORE_CFG, "domain", domain)
    monkeypatch.setattr(core_config.CORE_CFG, "web_url_path_prefix", prefix)
    predicate = predicate_from(web_configured)
    with pytest.raises(CheckFailure):
        predicate(MagicMock())


def test_web_configured_passes_when_set(monkeypatch):
    monkeypatch.setattr(core_config.CORE_CFG, "domain", "example.com")
    monkeypatch.setattr(core_config.CORE_CFG, "web_url_path_prefix", "secret")
    predicate = predicate_from(web_configured)
    assert predicate(MagicMock()) is True
