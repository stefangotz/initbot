# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import time

import pytest
from starlette.testclient import TestClient

import initbot_core.state.state as state_module
import initbot_web.routes.tracker as tracker_module
from initbot_core.data.character import NewCharacterData
from initbot_core.state.factory import create_state_from_source
from initbot_core.state.state import _SESSION_SECRET_TTL
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
        client.post(
            f"/testsecret/{app.state.admin_token}/"
        )  # sets session cookie in client's cookie jar
        yield client


# ── Login flow ────────────────────────────────────────────────────────────────


def test_login_get_shows_form(client, app):
    resp = client.get(f"/testsecret/{app.state.admin_token}/")
    assert resp.status_code == 200
    assert "Log In" in resp.text


def test_login_get_does_not_consume_token(tmp_path):
    """GET must not consume the token — bots (e.g. Discordbot) issue GET requests."""
    db_path = tmp_path / "test.db"
    state = create_state_from_source(f"sqlite:{db_path}")
    player = state.players.upsert(discord_id=42, name="Alice")
    assert player.discord_id is not None
    token = state.web_login_tokens.create(discord_id=player.discord_id)

    settings = WebSettings(state=f"sqlite:{db_path}")
    app = create_app(settings, web_url_path_prefix="admintoken")
    with TestClient(app, follow_redirects=False) as client:
        resp_get = client.get(f"/admintoken/{token}/")
        assert resp_get.status_code == 200  # login page, token NOT consumed
        resp_post = client.post(f"/admintoken/{token}/")
        assert resp_post.status_code == 303  # token consumed here
        assert resp_post.headers["location"] == "/admintoken/tracker/"


def test_login_post_redirects_to_tracker(client, app):
    resp = client.post(f"/testsecret/{app.state.admin_token}/")
    assert resp.status_code == 303
    assert resp.headers["location"] == "/testsecret/tracker/"


def test_login_get_invalid_token_returns_403(client):
    resp = client.get("/testsecret/wrongsecret/")
    assert resp.status_code == 403


def test_login_post_invalid_token_returns_403(client):
    resp = client.post("/testsecret/wrongsecret/")
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
    assert player.discord_id is not None
    token = state.web_login_tokens.create(discord_id=player.discord_id)

    settings = WebSettings(state=f"sqlite:{db_path}")
    app = create_app(settings, web_url_path_prefix="admintoken")
    with TestClient(app, follow_redirects=False) as client:
        client.post(f"/admintoken/{token}/")
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
    assert player.discord_id is not None
    token = state.web_login_tokens.create(discord_id=player.discord_id)

    settings = WebSettings(state=f"sqlite:{db_path}")
    app = create_app(settings, web_url_path_prefix="admintoken")
    with TestClient(app, follow_redirects=False) as client:
        resp = client.post(f"/admintoken/{token}/")
        assert resp.status_code == 303
        assert resp.headers["location"] == "/admintoken/tracker/"
        resp2 = client.get("/admintoken/tracker/", follow_redirects=False)
        assert resp2.status_code == 200
        assert "Initiative Order" in resp2.text


def test_used_token_returns_403(tmp_path):
    db_path = tmp_path / "test.db"
    state = create_state_from_source(f"sqlite:{db_path}")
    player = state.players.upsert(discord_id=43, name="Bob")
    assert player.discord_id is not None
    token = state.web_login_tokens.create(discord_id=player.discord_id)

    settings = WebSettings(state=f"sqlite:{db_path}")
    app = create_app(settings, web_url_path_prefix="admintoken")
    with TestClient(app, follow_redirects=False) as client:
        client.post(f"/admintoken/{token}/")  # first use — consumes the token
        resp_get = client.get(f"/admintoken/{token}/")  # GET after use — should fail
        assert resp_get.status_code == 403
        resp_post = client.post(f"/admintoken/{token}/")  # POST after use — should fail
        assert resp_post.status_code == 403


# ── Session expiry & logout ───────────────────────────────────────────────────


def test_expired_session_returns_403(app, monkeypatch):
    future = time.time() + tracker_module.SESSION_TTL + 1
    with TestClient(app, follow_redirects=False) as client:
        client.post(f"/testsecret/{app.state.admin_token}/")  # log in
        monkeypatch.setattr(tracker_module.time, "time", lambda: future)
        resp = client.get("/testsecret/tracker/")
        assert resp.status_code == 403


def test_logout_clears_session(authed_client):
    resp = authed_client.get("/testsecret/logout")
    assert resp.status_code == 200
    resp2 = authed_client.get("/testsecret/tracker/")
    assert resp2.status_code == 403


# ── Session secret persistence ────────────────────────────────────────────────


def test_session_survives_restart(tmp_path):
    """Session cookies remain valid when a new app instance reuses the unexpired secret."""
    settings = WebSettings(state=f"sqlite:{tmp_path / 'test.db'}")
    app1 = create_app(settings, web_url_path_prefix="testsecret")
    with TestClient(app1, follow_redirects=False) as client1:
        client1.post(f"/testsecret/{app1.state.admin_token}/")
        cookies = dict(client1.cookies)

    app2 = create_app(settings, web_url_path_prefix="testsecret")
    with TestClient(app2, follow_redirects=False) as client2:
        client2.cookies.update(cookies)
        resp = client2.get("/testsecret/tracker/")
        assert resp.status_code == 200


# ── set-initiative endpoint ───────────────────────────────────────────────────


def _make_app_with_character(tmp_path):
    """Return (app, state, char_name) with one character in the DB."""
    db_path = tmp_path / "test.db"
    state = create_state_from_source(f"sqlite:{db_path}")
    player = state.players.upsert(discord_id=99, name="Tester")
    assert player.id is not None
    char = state.characters.add_store_and_get(
        NewCharacterData(name="Aldric", player_id=player.id)
    )
    settings = WebSettings(state=f"sqlite:{db_path}")
    app = create_app(settings, web_url_path_prefix="testsecret")
    return app, state, char.name


def test_set_initiative_requires_auth(tmp_path):
    app, _, char_name = _make_app_with_character(tmp_path)
    with TestClient(app, follow_redirects=False) as client:
        resp = client.post(
            "/testsecret/tracker/set-initiative",
            json={"editchar": char_name, "initval": 10},
        )
        assert resp.status_code == 403


def test_set_initiative_updates_character(tmp_path):
    app, state, _ = _make_app_with_character(tmp_path)
    with TestClient(app, follow_redirects=False) as client:
        client.post(f"/testsecret/{app.state.admin_token}/")
        resp = client.post(
            "/testsecret/tracker/set-initiative",
            json={"editchar": "Aldric", "initval": 17},
        )
        assert resp.status_code == 200
        assert state.characters.get_from_name("Aldric").initiative == 17


def test_set_initiative_unknown_character_returns_2xx_no_change(tmp_path):
    app, _, _ = _make_app_with_character(tmp_path)
    with TestClient(app, follow_redirects=False) as client:
        client.post(f"/testsecret/{app.state.admin_token}/")
        resp = client.post(
            "/testsecret/tracker/set-initiative",
            json={"editchar": "NoSuchCharacter", "initval": 5},
        )
        assert resp.status_code in (200, 204)


def test_set_initiative_out_of_range_returns_error_signal(tmp_path):
    app, state, _ = _make_app_with_character(tmp_path)
    char = state.characters.get_from_name("Aldric")
    char.initiative = 10
    state.characters.update_and_store(char)
    with TestClient(app, follow_redirects=False) as client:
        client.post(f"/testsecret/{app.state.admin_token}/")
        resp = client.post(
            "/testsecret/tracker/set-initiative",
            json={"editchar": "Aldric", "initval": 999},
        )
        assert resp.status_code in (200, 204)
        assert state.characters.get_from_name("Aldric").initiative == 10
        assert "editerror" in resp.text


def test_set_initiative_missing_initval_returns_error_signal(tmp_path):
    app, _, _ = _make_app_with_character(tmp_path)
    with TestClient(app, follow_redirects=False) as client:
        client.post(f"/testsecret/{app.state.admin_token}/")
        resp = client.post(
            "/testsecret/tracker/set-initiative",
            json={"editchar": "Aldric"},
        )
        assert resp.status_code in (200, 204)
        assert "editerror" in resp.text


def test_set_initiative_invalid_input_returns_error_signal(tmp_path):
    app, _, _ = _make_app_with_character(tmp_path)
    with TestClient(app, follow_redirects=False) as client:
        client.post(f"/testsecret/{app.state.admin_token}/")
        resp = client.post(
            "/testsecret/tracker/set-initiative",
            json={"editchar": "Aldric", "initval": "notvalid"},
        )
        assert resp.status_code in (200, 204)
        assert "editerror" in resp.text


def test_set_initiative_dice_expression_stores_dice(tmp_path):
    app, state, _ = _make_app_with_character(tmp_path)
    with TestClient(app, follow_redirects=False) as client:
        client.post(f"/testsecret/{app.state.admin_token}/")
        resp = client.post(
            "/testsecret/tracker/set-initiative",
            json={"editchar": "Aldric", "initval": "d20+5"},
        )
        assert resp.status_code == 200
        assert state.characters.get_from_name("Aldric").initiative_dice == "d20+5"


def test_set_initiative_dice_expression_preserves_existing_initiative(tmp_path):
    app, state, _ = _make_app_with_character(tmp_path)
    char = state.characters.get_from_name("Aldric")
    char.initiative = 10
    state.characters.update_and_store(char)
    with TestClient(app, follow_redirects=False) as client:
        client.post(f"/testsecret/{app.state.admin_token}/")
        client.post(
            "/testsecret/tracker/set-initiative",
            json={"editchar": "Aldric", "initval": "d20+5"},
        )
        updated = state.characters.get_from_name("Aldric")
        assert updated.initiative_dice == "d20+5"
        assert updated.initiative == 10


def test_session_invalidated_after_secret_expiry(tmp_path, monkeypatch):
    """Sessions are invalidated when the signing secret has expired and is rotated."""
    settings = WebSettings(state=f"sqlite:{tmp_path / 'test.db'}")
    app1 = create_app(settings, web_url_path_prefix="testsecret")
    with TestClient(app1, follow_redirects=False) as client1:
        client1.post(f"/testsecret/{app1.state.admin_token}/")
        cookies = dict(client1.cookies)

    future = int(time.time()) + _SESSION_SECRET_TTL + 1
    monkeypatch.setattr(state_module.time, "time", lambda: future)

    app2 = create_app(settings, web_url_path_prefix="testsecret")
    with TestClient(app2, follow_redirects=False) as client2:
        client2.cookies.update(cookies)
        resp = client2.get("/testsecret/tracker/")
        assert resp.status_code == 403


# ── roll-initiative endpoint ──────────────────────────────────────────────────


def _make_app_with_dice(tmp_path, initiative_dice: str | None):
    """Return (app, state, char_name) with one character, optionally with initiative_dice."""
    db_path = tmp_path / "test.db"
    state = create_state_from_source(f"sqlite:{db_path}")
    player = state.players.upsert(discord_id=99, name="Tester")
    assert player.id is not None
    char = state.characters.add_store_and_get(
        NewCharacterData(
            name="Aldric", player_id=player.id, initiative_dice=initiative_dice
        )
    )
    settings = WebSettings(state=f"sqlite:{db_path}")
    app = create_app(settings, web_url_path_prefix="testsecret")
    return app, state, char.name


def test_roll_initiative_requires_auth(tmp_path):
    app, _, char_name = _make_app_with_dice(tmp_path, "d6")
    with TestClient(app, follow_redirects=False) as client:
        resp = client.post(f"/testsecret/tracker/roll-initiative/{char_name}")
        assert resp.status_code == 403


def test_roll_initiative_updates_character(tmp_path):
    app, state, _ = _make_app_with_dice(tmp_path, "d6")
    with TestClient(app, follow_redirects=False) as client:
        client.post(f"/testsecret/{app.state.admin_token}/")
        resp = client.post("/testsecret/tracker/roll-initiative/Aldric")
        assert resp.status_code in (200, 204)
        initiative = state.characters.get_from_name("Aldric").initiative
        assert initiative is not None
        assert 1 <= initiative <= 6


def test_roll_initiative_unknown_character_returns_2xx_no_change(tmp_path):
    app, _, _ = _make_app_with_dice(tmp_path, "d6")
    with TestClient(app, follow_redirects=False) as client:
        client.post(f"/testsecret/{app.state.admin_token}/")
        resp = client.post("/testsecret/tracker/roll-initiative/NoSuchCharacter")
        assert resp.status_code in (200, 204)


def test_roll_initiative_no_dice_set_returns_2xx_no_change(tmp_path):
    app, state, _ = _make_app_with_dice(tmp_path, None)
    with TestClient(app, follow_redirects=False) as client:
        client.post(f"/testsecret/{app.state.admin_token}/")
        resp = client.post("/testsecret/tracker/roll-initiative/Aldric")
        assert resp.status_code in (200, 204)
        assert state.characters.get_from_name("Aldric").initiative is None


def test_roll_initiative_invalid_dice_returns_2xx_no_change(tmp_path):
    app, state, _ = _make_app_with_dice(tmp_path, "notvalid")
    with TestClient(app, follow_redirects=False) as client:
        client.post(f"/testsecret/{app.state.admin_token}/")
        resp = client.post("/testsecret/tracker/roll-initiative/Aldric")
        assert resp.status_code in (200, 204)
        assert state.characters.get_from_name("Aldric").initiative is None
