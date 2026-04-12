# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import pytest

import initbot_core.state.state as state_module
from initbot_core.state.factory import create_state_from_source
from initbot_core.state.state import _SESSION_SECRET_TTL


@pytest.fixture(params=["json", "sqlite"], name="state")
def _state(request, tmp_path):
    if request.param == "json":
        return create_state_from_source(f"json:{tmp_path}")
    return create_state_from_source(f"sqlite:{tmp_path / 'test.db'}")


def test_get_or_rotate_returns_string(state):
    secret = state.session_secret.get_or_rotate()
    assert isinstance(secret, str)
    assert len(secret) > 0


def test_get_or_rotate_returns_same_secret_when_unexpired(state):
    secret1 = state.session_secret.get_or_rotate()
    secret2 = state.session_secret.get_or_rotate()
    assert secret1 == secret2


def test_get_or_rotate_replaces_secret_when_expired(state, monkeypatch):
    secret1 = state.session_secret.get_or_rotate()
    future = int(state_module.time.time()) + _SESSION_SECRET_TTL + 1
    monkeypatch.setattr(state_module.time, "time", lambda: future)
    secret2 = state.session_secret.get_or_rotate()
    assert secret2 != secret1


def test_get_or_rotate_new_secret_is_stable_after_rotation(state, monkeypatch):
    state.session_secret.get_or_rotate()
    future = int(state_module.time.time()) + _SESSION_SECRET_TTL + 1
    monkeypatch.setattr(state_module.time, "time", lambda: future)
    secret2 = state.session_secret.get_or_rotate()
    secret3 = state.session_secret.get_or_rotate()
    assert secret2 == secret3
