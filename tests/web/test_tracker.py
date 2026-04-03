# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import time

import pytest
from starlette.testclient import TestClient

import initbot_web.routes.tracker as tracker_module
from initbot_core.state.factory import create_state_from_source
from initbot_web.app import create_app
from initbot_web.config import WebSettings


@pytest.fixture(name="app")
def _app(tmp_path):
    settings = WebSettings(state=f"sqlite:{tmp_path / 'test.db'}")
    return create_app(settings, web_url_path_prefix="testsecret")


@pytest.fixture(name="client")
def _client(app):
    with TestClient(app, follow_redirects=False) as c:
        yield c


@pytest.fixture(name="authed_client")
def _authed_client(app):
    """Client with an active session obtained via the shared admin token."""
    with TestClient(app, follow_redirects=False) as client:
        client.get(
            "/testsecret/testsecret/"
        )  # sets session cookie in client's cookie jar
        yield client


# ── Login flow ────────────────────────────────────────────────────────────────


def test_valid_token_redirects_to_tracker(client):
    resp = client.get("/testsecret/testsecret/")
    assert resp.status_code == 302
    assert resp.headers["location"] == "/testsecret/tracker/"


def test_invalid_token_returns_403(client):
    resp = client.get("/testsecret/wrongsecret/")
    assert resp.status_code == 403


def test_unknown_prefix_returns_404(client):
    resp = client.get("/wrongprefix/testsecret/")
    assert resp.status_code == 404


# ── Tracker page ──────────────────────────────────────────────────────────────


def test_tracker_page_requires_session(client):
    resp = client.get("/testsecret/tracker/")
    assert resp.status_code == 403


def test_tracker_page_accessible_after_login(authed_client):
    resp = authed_client.get("/testsecret/tracker/", follow_redirects=False)
    assert resp.status_code == 200
    assert "Initiative Order" in resp.text


def test_tracker_page_shows_player_name(tmp_path):
    db_path = tmp_path / "test.db"
    state = create_state_from_source(f"sqlite:{db_path}")
    player = state.players.upsert(discord_id=44, name="Alice")
    token = state.web_login_tokens.create(discord_id=player.discord_id)

    settings = WebSettings(state=f"sqlite:{db_path}")
    app = create_app(settings, web_url_path_prefix="admintoken")
    with TestClient(app, follow_redirects=False) as client:
        client.get(f"/admintoken/{token}/")
        resp = client.get("/admintoken/tracker/", follow_redirects=False)
        assert resp.status_code == 200
        assert "Alice" in resp.text


def test_tracker_page_no_player_name_for_admin_session(authed_client):
    resp = authed_client.get("/testsecret/tracker/")
    assert resp.status_code == 200
    assert 'id="player-bar"' not in resp.text


# ── SSE endpoint ──────────────────────────────────────────────────────────────


def test_sse_requires_session(client):
    resp = client.get("/testsecret/tracker/sse")
    assert resp.status_code == 403


# ── Per-player token flow ────────────────────────────────────────────────────


def test_per_player_token_creates_session(tmp_path):
    db_path = tmp_path / "test.db"
    state = create_state_from_source(f"sqlite:{db_path}")
    player = state.players.upsert(discord_id=42, name="Alice")
    token = state.web_login_tokens.create(discord_id=player.discord_id)

    settings = WebSettings(state=f"sqlite:{db_path}")
    app = create_app(settings, web_url_path_prefix="admintoken")
    with TestClient(app, follow_redirects=False) as client:
        resp = client.get(f"/admintoken/{token}/")
        assert resp.status_code == 302
        assert resp.headers["location"] == "/admintoken/tracker/"
        resp2 = client.get("/admintoken/tracker/", follow_redirects=False)
        assert resp2.status_code == 200
        assert "Initiative Order" in resp2.text


def test_used_token_returns_403(tmp_path):
    db_path = tmp_path / "test.db"
    state = create_state_from_source(f"sqlite:{db_path}")
    player = state.players.upsert(discord_id=43, name="Bob")
    token = state.web_login_tokens.create(discord_id=player.discord_id)

    settings = WebSettings(state=f"sqlite:{db_path}")
    app = create_app(settings, web_url_path_prefix="admintoken")
    with TestClient(app, follow_redirects=False) as client:
        client.get(f"/admintoken/{token}/")  # first use — consumes the token
        resp = client.get(f"/admintoken/{token}/")  # second use — should fail
        assert resp.status_code == 403


# ── Session expiry & logout ───────────────────────────────────────────────────


def test_expired_session_returns_403(app, monkeypatch):
    future = time.time() + tracker_module.SESSION_TTL + 1
    with TestClient(app, follow_redirects=False) as client:
        client.get("/testsecret/testsecret/")  # log in (session written at real now)
        monkeypatch.setattr(tracker_module.time, "time", lambda: future)
        resp = client.get("/testsecret/tracker/")
        assert resp.status_code == 403


def test_logout_clears_session(authed_client):
    resp = authed_client.get("/testsecret/logout")
    assert resp.status_code == 200
    resp2 = authed_client.get("/testsecret/tracker/")
    assert resp2.status_code == 403
