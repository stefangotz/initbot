# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from unittest.mock import MagicMock

import pytest
from discord.ext.commands import CheckFailure

import initbot_core.config as core_config
from initbot_chat.commands.utils import (
    abilities_required,
    augurs_required,
    classes_required,
    crits_required,
    occupations_required,
    web_configured,
)
from tests.helpers import predicate_from

_STATE_CHECKS = [
    (abilities_required, "abilities"),
    (augurs_required, "augurs"),
    (classes_required, "classes"),
    (occupations_required, "occupations"),
    (crits_required, "crits"),
]


def _ctx_with(attr: str, populated: bool) -> MagicMock:
    ctx = MagicMock()
    getattr(ctx.bot.initbot_state, attr).get_all.return_value = (
        [MagicMock()] if populated else []
    )
    return ctx


@pytest.mark.parametrize(("check_decorator", "state_attr"), _STATE_CHECKS)
def test_state_check_raises_when_empty(check_decorator, state_attr):
    predicate = predicate_from(check_decorator)
    ctx = _ctx_with(state_attr, populated=False)
    with pytest.raises(CheckFailure):
        predicate(ctx)


@pytest.mark.parametrize(("check_decorator", "state_attr"), _STATE_CHECKS)
def test_state_check_passes_when_populated(check_decorator, state_attr):
    predicate = predicate_from(check_decorator)
    ctx = _ctx_with(state_attr, populated=True)
    assert predicate(ctx) is True


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
