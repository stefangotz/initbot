# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import socket
import time

import pytest
from starlette.testclient import TestClient

import initbot_core.state.state as state_module
import initbot_web.routes.tracker as tracker_module
from initbot_core.data.character import CharacterData, NewCharacterData
from initbot_core.data.player import PlayerData
from initbot_core.state.factory import create_state_from_source
from initbot_core.state.state import _SESSION_SECRET_TTL
from initbot_web.app import create_app
from initbot_web.config import WebSettings
from initbot_web.routes.tracker import (
    _STALE_INIT,
    _compute_desired_ranked,
    _has_valid_dice,
    _inline_blur,
    _inline_click_switch,
    _is_initiative_eligible,
    _render_alert,
    _render_combined_rows,
    _render_delete_button,
    _render_inline_dice_cell,
    _render_inline_init_cell,
    _render_inline_name_cell,
    _render_inline_player_cell,
    _render_player_options,
    _render_roll_button,
    _render_sort_indicator,
    _resolve_player_name,
    _safe_dice,
    _safe_int,
)


def _free_udp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(name="app")
def _app(tmp_path):
    settings = WebSettings(
        state=f"sqlite:{tmp_path / 'test.db'}", notify_port=_free_udp_port()
    )
    return create_app(settings, web_url_path_prefix="testsecret")


@pytest.fixture(name="client")
def _client(app):
    with TestClient(app, follow_redirects=False) as c:
        yield c


@pytest.fixture(name="authed_client")
def _authed_client(app):
    """Client with an active session obtained via the join flow."""
    with TestClient(app, follow_redirects=False) as client:
        client.post("/testsecret/join/", data={"name": "Tester"})
        yield client


# ── Login flow ────────────────────────────────────────────────────────────────


def test_join_get_shows_form(client):
    resp = client.get("/testsecret/join/")
    assert resp.status_code == 200
    assert "Join" in resp.text


def test_login_get_does_not_consume_token(tmp_path):
    """GET must not consume the token — bots (e.g. Discordbot) issue GET requests."""
    db_path = tmp_path / "test.db"
    state = create_state_from_source(f"sqlite:{db_path}")
    player = state.players.upsert_discord(discord_id=42, name="Alice")
    assert player.discord_id is not None
    token = state.web_login_tokens.create(discord_id=player.discord_id)

    settings = WebSettings(state=f"sqlite:{db_path}", notify_port=_free_udp_port())
    app = create_app(settings, web_url_path_prefix="admintoken")
    with TestClient(app, follow_redirects=False) as client:
        resp_get = client.get(f"/admintoken/{token}/")
        assert resp_get.status_code == 200  # login page, token NOT consumed
        resp_post = client.post(f"/admintoken/{token}/")
        assert resp_post.status_code == 303  # token consumed here
        assert resp_post.headers["location"] == "/admintoken/tracker/"


def test_join_post_redirects_to_tracker(client):
    resp = client.post("/testsecret/join/", data={"name": "Tester"})
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
    player = state.players.upsert_discord(discord_id=44, name="Alice")
    assert player.discord_id is not None
    token = state.web_login_tokens.create(discord_id=player.discord_id)

    settings = WebSettings(state=f"sqlite:{db_path}", notify_port=_free_udp_port())
    app = create_app(settings, web_url_path_prefix="admintoken")
    with TestClient(app, follow_redirects=False) as client:
        client.post(f"/admintoken/{token}/")
        resp = client.get("/admintoken/tracker/", follow_redirects=False)
        assert resp.status_code == 200
        assert "Alice" in resp.text


def test_tracker_page_shows_player_name_for_join_session(authed_client):
    resp = authed_client.get("/testsecret/tracker/")
    assert resp.status_code == 200
    assert "Tester" in resp.text


# ── SSE endpoint ──────────────────────────────────────────────────────────────


def test_sse_requires_session(client):
    resp = client.get("/testsecret/tracker/sse")
    assert resp.status_code == 403


# ── Per-player token flow ────────────────────────────────────────────────────


def test_per_player_token_creates_session(tmp_path):
    db_path = tmp_path / "test.db"
    state = create_state_from_source(f"sqlite:{db_path}")
    player = state.players.upsert_discord(discord_id=42, name="Alice")
    assert player.discord_id is not None
    token = state.web_login_tokens.create(discord_id=player.discord_id)

    settings = WebSettings(state=f"sqlite:{db_path}", notify_port=_free_udp_port())
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
    player = state.players.upsert_discord(discord_id=43, name="Bob")
    assert player.discord_id is not None
    token = state.web_login_tokens.create(discord_id=player.discord_id)

    settings = WebSettings(state=f"sqlite:{db_path}", notify_port=_free_udp_port())
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
        client.post("/testsecret/join/", data={"name": "Tester"})  # log in
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
    settings = WebSettings(
        state=f"sqlite:{tmp_path / 'test.db'}", notify_port=_free_udp_port()
    )
    app1 = create_app(settings, web_url_path_prefix="testsecret")
    with TestClient(app1, follow_redirects=False) as client1:
        client1.post("/testsecret/join/", data={"name": "Tester"})
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
    player = state.players.upsert_discord(discord_id=99, name="Alice")
    assert player.id is not None
    char = state.characters.add_store_and_get(
        NewCharacterData(name="Aldric", player_id=player.id)
    )
    settings = WebSettings(state=f"sqlite:{db_path}", notify_port=_free_udp_port())
    app = create_app(settings, web_url_path_prefix="testsecret")
    return app, state, char.name


def test_set_initiative_requires_auth(tmp_path):
    app, _, char_name = _make_app_with_character(tmp_path)
    with TestClient(app, follow_redirects=False) as client:
        resp = client.post(
            "/testsecret/tracker/add-character",
            json={"editchar": char_name, "initval": 10},
        )
        assert resp.status_code == 403


def test_set_initiative_updates_character(tmp_path):
    app, state, _ = _make_app_with_character(tmp_path)
    with TestClient(app, follow_redirects=False) as client:
        client.post("/testsecret/join/", data={"name": "Tester"})
        resp = client.post(
            "/testsecret/tracker/add-character",
            json={"editchar": "Aldric", "initval": 17},
        )
        assert resp.status_code == 200
        assert state.characters.get_from_name("Aldric").initiative == 17


def test_set_initiative_unknown_character_returns_2xx_no_change(tmp_path):
    app, _, _ = _make_app_with_character(tmp_path)
    with TestClient(app, follow_redirects=False) as client:
        client.post("/testsecret/join/", data={"name": "Tester"})
        resp = client.post(
            "/testsecret/tracker/add-character",
            json={"editchar": "NoSuchCharacter", "initval": 5},
        )
        assert resp.status_code in (200, 204)


def test_set_initiative_out_of_range_returns_error_signal(tmp_path):
    app, state, _ = _make_app_with_character(tmp_path)
    char = state.characters.get_from_name("Aldric")
    char.initiative = 10
    state.characters.update_and_store(char)
    with TestClient(app, follow_redirects=False) as client:
        client.post("/testsecret/join/", data={"name": "Tester"})
        resp = client.post(
            "/testsecret/tracker/add-character",
            json={"editchar": "Aldric", "initval": 999},
        )
        assert resp.status_code in (200, 204)
        assert state.characters.get_from_name("Aldric").initiative == 10
        assert "editerror" in resp.text


def test_set_initiative_missing_initval_leaves_initiative_unchanged(tmp_path):
    app, state, _ = _make_app_with_character(tmp_path)
    char = state.characters.get_from_name("Aldric")
    char.initiative = 12
    char.initiative_dice = "d20+3"
    state.characters.update_and_store(char)
    with TestClient(app, follow_redirects=False) as client:
        client.post("/testsecret/join/", data={"name": "Tester"})
        client.post(
            "/testsecret/tracker/add-character",
            json={"editchar": "Aldric"},
        )
        updated = state.characters.get_from_name("Aldric")
        assert updated.initiative == 12
        assert updated.initiative_dice == "d20+3"


def test_set_initiative_invalid_input_returns_error_signal(tmp_path):
    app, _, _ = _make_app_with_character(tmp_path)
    with TestClient(app, follow_redirects=False) as client:
        client.post("/testsecret/join/", data={"name": "Tester"})
        resp = client.post(
            "/testsecret/tracker/add-character",
            json={"editchar": "Aldric", "initval": "notvalid"},
        )
        assert resp.status_code in (200, 204)
        assert "editerror" in resp.text


def test_set_initiative_dice_expression_stores_dice(tmp_path):
    app, state, _ = _make_app_with_character(tmp_path)
    with TestClient(app, follow_redirects=False) as client:
        client.post("/testsecret/join/", data={"name": "Tester"})
        resp = client.post(
            "/testsecret/tracker/add-character",
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
        client.post("/testsecret/join/", data={"name": "Tester"})
        client.post(
            "/testsecret/tracker/add-character",
            json={"editchar": "Aldric", "initval": "d20+5"},
        )
        updated = state.characters.get_from_name("Aldric")
        assert updated.initiative_dice == "d20+5"
        assert updated.initiative == 10


def test_session_invalidated_after_secret_expiry(tmp_path, monkeypatch):
    """Sessions are invalidated when the signing secret has expired and is rotated."""
    settings = WebSettings(
        state=f"sqlite:{tmp_path / 'test.db'}", notify_port=_free_udp_port()
    )
    app1 = create_app(settings, web_url_path_prefix="testsecret")
    with TestClient(app1, follow_redirects=False) as client1:
        client1.post("/testsecret/join/", data={"name": "Tester"})
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
    player = state.players.upsert_discord(discord_id=99, name="Alice")
    assert player.id is not None
    char = state.characters.add_store_and_get(
        NewCharacterData(
            name="Aldric", player_id=player.id, initiative_dice=initiative_dice
        )
    )
    settings = WebSettings(state=f"sqlite:{db_path}", notify_port=_free_udp_port())
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
        client.post("/testsecret/join/", data={"name": "Tester"})
        resp = client.post("/testsecret/tracker/roll-initiative/Aldric")
        assert resp.status_code in (200, 204)
        initiative = state.characters.get_from_name("Aldric").initiative
        assert initiative is not None
        assert 1 <= initiative <= 6


def test_roll_initiative_unknown_character_returns_2xx_no_change(tmp_path):
    app, _, _ = _make_app_with_dice(tmp_path, "d6")
    with TestClient(app, follow_redirects=False) as client:
        client.post("/testsecret/join/", data={"name": "Tester"})
        resp = client.post("/testsecret/tracker/roll-initiative/NoSuchCharacter")
        assert resp.status_code in (200, 204)


def test_roll_initiative_no_dice_set_returns_2xx_no_change(tmp_path):
    app, state, _ = _make_app_with_dice(tmp_path, None)
    with TestClient(app, follow_redirects=False) as client:
        client.post("/testsecret/join/", data={"name": "Tester"})
        resp = client.post("/testsecret/tracker/roll-initiative/Aldric")
        assert resp.status_code in (200, 204)
        assert state.characters.get_from_name("Aldric").initiative is None


def test_roll_initiative_invalid_dice_returns_2xx_no_change(tmp_path):
    app, state, _ = _make_app_with_dice(tmp_path, "notvalid")
    with TestClient(app, follow_redirects=False) as client:
        client.post("/testsecret/join/", data={"name": "Tester"})
        resp = client.post("/testsecret/tracker/roll-initiative/Aldric")
        assert resp.status_code in (200, 204)
        assert state.characters.get_from_name("Aldric").initiative is None


# ── resort-initiative endpoint ───────────────────────────────────────────────


def test_resort_requires_auth(tmp_path):
    app, _, _ = _make_app_with_character(tmp_path)
    with TestClient(app, follow_redirects=False) as client:
        resp = client.post("/testsecret/tracker/resort")
        assert resp.status_code == 403


def test_resort_returns_2xx_when_authed(tmp_path):
    app, _, _ = _make_app_with_character(tmp_path)
    with TestClient(app, follow_redirects=False) as client:
        client.post("/testsecret/join/", data={"name": "Tester"})
        resp = client.post("/testsecret/tracker/resort")
        assert resp.status_code in (200, 204)


# ── Edit character name and player ────────────────────────────────────────────


def _make_app_with_two_players(tmp_path):
    """Return (app, state, char, player1, player2) with one character owned by player1."""
    db_path = tmp_path / "test.db"
    state = create_state_from_source(f"sqlite:{db_path}")
    player1 = state.players.upsert_discord(discord_id=10, name="Alice")
    player2 = state.players.upsert_discord(discord_id=20, name="Bob")
    char = state.characters.add_store_and_get(
        NewCharacterData(name="Gandalf", player_id=player1.id)
    )
    settings = WebSettings(state=f"sqlite:{db_path}", notify_port=_free_udp_port())
    app = create_app(settings, web_url_path_prefix="testsecret")
    return app, state, char, player1, player2


def test_rename_character(tmp_path):
    app, state, _, _, _ = _make_app_with_two_players(tmp_path)
    with TestClient(app, follow_redirects=False) as client:
        client.post("/testsecret/join/", data={"name": "Tester"})
        resp = client.post(
            "/testsecret/tracker/add-character",
            json={"editchar": "Gandalf", "newcharname": "Gandalf the White"},
        )
        assert resp.status_code == 200
        all_names = [c.name for c in state.characters.get_all()]
        assert "Gandalf the White" in all_names
        assert "Gandalf" not in all_names


def test_rename_to_existing_name_returns_error(tmp_path):
    app, state, _, player1, _ = _make_app_with_two_players(tmp_path)
    state.characters.add_store_and_get(
        NewCharacterData(name="Saruman", player_id=player1.id)
    )
    with TestClient(app, follow_redirects=False) as client:
        client.post("/testsecret/join/", data={"name": "Tester"})
        resp = client.post(
            "/testsecret/tracker/add-character",
            json={"editchar": "Gandalf", "newcharname": "Saruman"},
        )
        assert resp.status_code in (200, 204)
        assert "nameerror" in resp.text
        assert state.characters.get_from_name("Gandalf") is not None


def test_change_character_player(tmp_path):
    app, state, _, _, player2 = _make_app_with_two_players(tmp_path)
    with TestClient(app, follow_redirects=False) as client:
        client.post("/testsecret/join/", data={"name": "Tester"})
        resp = client.post(
            "/testsecret/tracker/add-character",
            json={"editchar": "Gandalf", "editplayerid": str(player2.id)},
        )
        assert resp.status_code == 200
        assert state.characters.get_from_name("Gandalf").player_id == player2.id


def test_change_character_player_invalid_id_ignored(tmp_path):
    app, state, _, player1, _ = _make_app_with_two_players(tmp_path)
    with TestClient(app, follow_redirects=False) as client:
        client.post("/testsecret/join/", data={"name": "Tester"})
        resp = client.post(
            "/testsecret/tracker/add-character",
            json={"editchar": "Gandalf", "editplayerid": "9999"},
        )
        assert resp.status_code == 200
        assert state.characters.get_from_name("Gandalf").player_id == player1.id


def test_rename_and_change_player_together(tmp_path):
    app, state, _, _, player2 = _make_app_with_two_players(tmp_path)
    with TestClient(app, follow_redirects=False) as client:
        client.post("/testsecret/join/", data={"name": "Tester"})
        resp = client.post(
            "/testsecret/tracker/add-character",
            json={
                "editchar": "Gandalf",
                "newcharname": "Gandalf the White",
                "editplayerid": str(player2.id),
            },
        )
        assert resp.status_code == 200
        updated = state.characters.get_from_name("Gandalf the White")
        assert updated is not None
        assert updated.player_id == player2.id


# ── Create character ──────────────────────────────────────────────────────────


def test_create_character_creates_new_character(tmp_path):
    app, state, _ = _make_app_with_character(tmp_path)
    with TestClient(app, follow_redirects=False) as client:
        client.post("/testsecret/join/", data={"name": "Tester"})
        resp = client.post(
            "/testsecret/tracker/add-character",
            json={"editchar": "", "newcharname": "Fenix", "initval": "12"},
        )
        assert resp.status_code == 200
        names = [c.name for c in state.characters.get_all()]
        assert "Fenix" in names


def test_create_character_with_dice_expression(tmp_path):
    app, state, _ = _make_app_with_character(tmp_path)
    with TestClient(app, follow_redirects=False) as client:
        client.post("/testsecret/join/", data={"name": "Tester"})
        resp = client.post(
            "/testsecret/tracker/add-character",
            json={"editchar": "", "newcharname": "Fenix", "initval": "d20+3"},
        )
        assert resp.status_code == 200
        char = state.characters.get_from_name("Fenix")
        assert char.initiative_dice == "d20+3"


def test_create_character_empty_name_is_noop(tmp_path):
    app, state, _ = _make_app_with_character(tmp_path)
    count_before = len(state.characters.get_all())
    with TestClient(app, follow_redirects=False) as client:
        client.post("/testsecret/join/", data={"name": "Tester"})
        resp = client.post(
            "/testsecret/tracker/add-character",
            json={"editchar": "", "newcharname": "", "initval": "5"},
        )
        assert resp.status_code in (200, 204)
        assert len(state.characters.get_all()) == count_before


def test_create_character_invalid_name_returns_error(tmp_path):
    app, _, _ = _make_app_with_character(tmp_path)
    with TestClient(app, follow_redirects=False) as client:
        client.post("/testsecret/join/", data={"name": "Tester"})
        # Control characters are invalid per validate_character_name
        resp = client.post(
            "/testsecret/tracker/add-character",
            json={"editchar": "", "newcharname": "Bad\x00Name", "initval": "5"},
        )
        assert resp.status_code in (200, 204)
        assert "nameerror" in resp.text


def test_create_character_duplicate_name_returns_error(tmp_path):
    app, _, char_name = _make_app_with_character(tmp_path)
    with TestClient(app, follow_redirects=False) as client:
        client.post("/testsecret/join/", data={"name": "Tester"})
        resp = client.post(
            "/testsecret/tracker/add-character",
            json={"editchar": "", "newcharname": char_name, "initval": "5"},
        )
        assert resp.status_code in (200, 204)
        assert "nameerror" in resp.text


def test_create_character_invalid_init_returns_error(tmp_path):
    app, _, _ = _make_app_with_character(tmp_path)
    with TestClient(app, follow_redirects=False) as client:
        client.post("/testsecret/join/", data={"name": "Tester"})
        resp = client.post(
            "/testsecret/tracker/add-character",
            json={"editchar": "", "newcharname": "Fenix", "initval": "notvalid"},
        )
        assert resp.status_code in (200, 204)
        assert "editerror" in resp.text


# ── Delete character ──────────────────────────────────────────────────────────


def test_delete_character_requires_auth(tmp_path):
    app, _, char_name = _make_app_with_character(tmp_path)
    with TestClient(app, follow_redirects=False) as client:
        resp = client.post(f"/testsecret/tracker/delete-character/{char_name}")
        assert resp.status_code == 403


def test_delete_character_removes_character(tmp_path):
    app, state, char_name = _make_app_with_character(tmp_path)
    with TestClient(app, follow_redirects=False) as client:
        client.post("/testsecret/join/", data={"name": "Tester"})
        resp = client.post(f"/testsecret/tracker/delete-character/{char_name}")
        assert resp.status_code in (200, 204)
        names = [c.name for c in state.characters.get_all()]
        assert char_name not in names


def test_delete_character_unknown_is_noop(tmp_path):
    app, state, _ = _make_app_with_character(tmp_path)
    count_before = len(state.characters.get_all())
    with TestClient(app, follow_redirects=False) as client:
        client.post("/testsecret/join/", data={"name": "Tester"})
        resp = client.post("/testsecret/tracker/delete-character/NoSuchCharacter")
        assert resp.status_code in (200, 204)
        assert len(state.characters.get_all()) == count_before


# ── nextfield / Tab-cycling server response ───────────────────────────────────


def test_nextfield_player_returns_editplayerid(tmp_path):
    app, state, _ = _make_app_with_character(tmp_path)
    char = state.characters.get_from_name("Aldric")
    with TestClient(app, follow_redirects=False) as client:
        client.post("/testsecret/join/", data={"name": "Tester"})
        resp = client.post(
            "/testsecret/tracker/add-character",
            json={
                "editchar": "Aldric",
                "initval": "15",
                "nextchar": "Aldric",
                "nextfield": "player",
            },
        )
        assert resp.status_code == 200
        assert "editingfield" in resp.text
        assert "player" in resp.text
        assert str(char.player_id) in resp.text


def test_nextfield_init_returns_initval(tmp_path):
    app, state, _ = _make_app_with_character(tmp_path)
    char = state.characters.get_from_name("Aldric")
    char.initiative = 17
    state.characters.update_and_store(char)
    with TestClient(app, follow_redirects=False) as client:
        client.post("/testsecret/join/", data={"name": "Tester"})
        resp = client.post(
            "/testsecret/tracker/add-character",
            json={
                "editchar": "Aldric",
                "initval": "18",
                "nextchar": "Aldric",
                "nextfield": "init",
            },
        )
        assert resp.status_code == 200
        assert "initval" in resp.text
        assert "18" in resp.text  # next char now has init 18


def test_nextfield_dice_returns_initval(tmp_path):
    app, state, _ = _make_app_with_character(tmp_path)
    char = state.characters.get_from_name("Aldric")
    char.initiative = 10
    char.initiative_dice = "d20+2"
    state.characters.update_and_store(char)
    with TestClient(app, follow_redirects=False) as client:
        client.post("/testsecret/join/", data={"name": "Tester"})
        resp = client.post(
            "/testsecret/tracker/add-character",
            json={
                "editchar": "Aldric",
                "initval": "12",
                "nextchar": "Aldric",
                "nextfield": "dice",
            },
        )
        assert resp.status_code == 200
        assert "initval" in resp.text
        assert "d20+2" in resp.text


def test_nextfield_name_returns_newcharname(tmp_path):
    app, _, _ = _make_app_with_character(tmp_path)
    with TestClient(app, follow_redirects=False) as client:
        client.post("/testsecret/join/", data={"name": "Tester"})
        resp = client.post(
            "/testsecret/tracker/add-character",
            json={
                "editchar": "Aldric",
                "initval": "10",
                "nextchar": "Aldric",
                "nextfield": "name",
            },
        )
        assert resp.status_code == 200
        assert "newcharname" in resp.text
        assert "Aldric" in resp.text


def test_nextfield_unknown_nextchar_falls_back_to_result(tmp_path):
    app, _, _ = _make_app_with_character(tmp_path)
    with TestClient(app, follow_redirects=False) as client:
        client.post("/testsecret/join/", data={"name": "Tester"})
        resp = client.post(
            "/testsecret/tracker/add-character",
            json={
                "editchar": "Aldric",
                "initval": "10",
                "nextchar": "NoSuchCharacter",
                "nextfield": "name",
            },
        )
        assert resp.status_code == 200
        assert "newcharname" in resp.text


# ── Helper function unit tests ─────────────────────────────────────────────────


def test_is_initiative_eligible_with_valid_data():
    now = int(time.time())
    char = CharacterData(name="X", player_id=1, initiative=10, last_used=now - 100)
    assert _is_initiative_eligible(char, now) is True


def test_is_initiative_eligible_no_initiative():
    now = int(time.time())
    char = CharacterData(name="X", player_id=1, initiative=None, last_used=now - 100)
    assert _is_initiative_eligible(char, now) is False


def test_compute_desired_ranked_sorts_descending():
    now = int(time.time())
    chars = [
        CharacterData(name="A", player_id=1, initiative=5, last_used=now),
        CharacterData(name="B", player_id=1, initiative=15, last_used=now),
        CharacterData(name="C", player_id=1, initiative=10, last_used=now),
    ]
    assert _compute_desired_ranked(chars, now) == ["B", "C", "A"]


def test_resolve_player_name_found():
    player = PlayerData(id=1, discord_id=100, name="Alice")
    char = CharacterData(name="X", player_id=1)
    assert _resolve_player_name({1: player}, char) == "Alice"


def test_resolve_player_name_not_found():
    char = CharacterData(name="X", player_id=99)
    assert _resolve_player_name({}, char) == "?"


def test_render_alert_with_vulnerability():
    html_out = _render_alert(True)
    assert "security-alert" in html_out
    assert "security update" in html_out


def test_render_alert_without_vulnerability():
    html_out = _render_alert(False)
    assert "security-alert" in html_out
    assert "security update" not in html_out


def test_render_player_options():
    players = [
        PlayerData(id=1, discord_id=10, name="Alice"),
        PlayerData(id=2, discord_id=20, name="Bob & Carol"),
    ]
    html_out = _render_player_options(players)
    assert 'value="1"' in html_out
    assert "Alice" in html_out
    assert "Bob &amp; Carol" in html_out


def test_has_valid_dice():
    assert _has_valid_dice("d20+3") is True
    assert _has_valid_dice("notdice") is False
    assert _has_valid_dice(None) is False
    assert _has_valid_dice("") is False


def test_render_roll_button_contains_char_name():
    html_out = _render_roll_button("Aldric", "/prefix")
    assert "roll-btn" in html_out
    assert "Aldric" in html_out
    assert "/prefix/" in html_out


def test_render_delete_button_contains_char_name():
    html_out = _render_delete_button("Brother Thog", "/del")
    assert "del-btn" in html_out
    assert "Brother%20Thog" in html_out


def test_render_sort_indicator_stale():
    html_out = _render_sort_indicator(True, "/resort")
    assert "resort-btn" in html_out
    assert "/resort" in html_out


def test_render_sort_indicator_not_stale():
    html_out = _render_sort_indicator(False, "/resort")
    assert "resort-btn" not in html_out
    assert "sort-indicator" in html_out


def test_inline_click_switch_contains_fields():
    expr = _inline_click_switch("init", "/add", "direct")
    assert "nextfield" in expr
    assert "'init'" in expr
    assert "direct" in expr


def test_inline_blur_contains_field():
    expr = _inline_blur("name")
    assert "$editingfield==='name'" in expr
    assert "setTimeout" in expr


def test_render_inline_name_cell():
    html_out = _render_inline_name_cell("Aldric", "/add")
    assert "Aldric" in html_out
    assert "editable" in html_out
    assert "newcharname" in html_out
    assert "/add" in html_out


def test_render_inline_name_cell_escapes_html():
    html_out = _render_inline_name_cell("<Scary>", "/add")
    assert "&lt;Scary&gt;" in html_out


def test_render_inline_player_cell():
    players = [PlayerData(id=1, discord_id=10, name="Alice")]
    html_out = _render_inline_player_cell("Alice", players, "/add")
    assert "Alice" in html_out
    assert "inline-select" in html_out
    assert "editplayerid" in html_out


def test_render_inline_init_cell_with_value():
    html_out = _render_inline_init_cell("15", "/add")
    assert "15" in html_out
    assert "initval" in html_out
    assert "editable-empty" not in html_out


def test_render_inline_init_cell_empty():
    assert "editable-empty" in _render_inline_init_cell("—", "/add")


def test_render_inline_dice_cell_with_value():
    html_out = _render_inline_dice_cell("d20+3", "/add")
    assert "d20+3" in html_out
    assert "editable-empty" not in html_out


def test_render_inline_dice_cell_empty():
    html_out = _render_inline_dice_cell(None, "/add")
    assert "—" in html_out
    assert "editable-empty" in html_out


def test_safe_int_and_dice():
    assert _safe_int(42) == "42"
    assert _safe_int(None) == ""
    assert _safe_dice("d20+3") == "d20+3"
    assert _safe_dice(None) == ""
    assert _safe_dice("") == ""


def test_render_combined_rows_produces_tbody():
    now = int(time.time())
    players = [PlayerData(id=1, discord_id=10, name="Alice")]
    chars = [
        (
            CharacterData(name="Aldric", player_id=1, initiative=18, last_used=now),
            "Alice",
        ),
        (
            CharacterData(name="Tara", player_id=1, initiative=None, last_used=now),
            "Alice",
        ),
    ]
    html_out = _render_combined_rows(
        chars, 1, frozenset(), "/roll", "/del", players, "/add"
    )
    assert 'id="char-rows"' in html_out
    assert "Aldric" in html_out
    assert "Tara" in html_out
    assert "group-separator" in html_out


def test_render_combined_rows_stale_init():
    now = int(time.time())
    players = [PlayerData(id=1, discord_id=10, name="Alice")]
    chars = [
        (
            CharacterData(name="Aldric", player_id=1, initiative=18, last_used=now),
            "Alice",
        )
    ]
    html_out = _render_combined_rows(
        chars, 1, frozenset({"Aldric"}), "/roll", "/del", players, "/add"
    )
    assert _STALE_INIT in html_out


def test_rename_character_invalid_name_returns_error(tmp_path):
    app, state, _, _, _ = _make_app_with_two_players(tmp_path)
    with TestClient(app, follow_redirects=False) as client:
        client.post("/testsecret/join/", data={"name": "Tester"})
        # Control characters are invalid per validate_character_name
        resp = client.post(
            "/testsecret/tracker/add-character",
            json={"editchar": "Gandalf", "newcharname": "Bad\x00Name"},
        )
        assert resp.status_code in (200, 204)
        assert "nameerror" in resp.text
        assert state.characters.get_from_name("Gandalf") is not None
