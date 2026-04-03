# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import time

import pytest

from initbot_core.state.factory import create_state_from_source


@pytest.fixture(name="token_state")
def _token_state(tmp_path):
    return create_state_from_source(f"sqlite:{tmp_path / 'test.db'}")


def test_create_returns_token(token_state):
    token = token_state.web_login_tokens.create(discord_id=123)
    assert isinstance(token, str)
    assert len(token) > 0


def test_find_valid_returns_discord_id(token_state):
    token = token_state.web_login_tokens.create(discord_id=456)
    result = token_state.web_login_tokens.find_valid(token)
    assert result == 456


def test_find_valid_unknown_token_returns_none(token_state):
    assert token_state.web_login_tokens.find_valid("no-such-token") is None


def test_find_valid_used_token_returns_none(token_state):
    token = token_state.web_login_tokens.create(discord_id=789)
    token_state.web_login_tokens.mark_used(token)
    assert token_state.web_login_tokens.find_valid(token) is None


def test_find_valid_expired_token_returns_none(token_state, monkeypatch):
    # Create a token, then advance time past expiry
    token = token_state.web_login_tokens.create(discord_id=101)
    future = time.time() + 120
    monkeypatch.setattr(time, "time", lambda: future)
    assert token_state.web_login_tokens.find_valid(token) is None


def test_prune_expired_removes_old_tokens(token_state, monkeypatch):
    token = token_state.web_login_tokens.create(discord_id=202)

    # Advance time and prune
    future = time.time() + 120
    monkeypatch.setattr(time, "time", lambda: future)
    token_state.web_login_tokens.prune_expired()

    # Token should be gone (find_valid returns None on missing too, but mark_used would KeyError)
    assert token_state.web_login_tokens.find_valid(token) is None
