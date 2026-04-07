# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import pytest


def test_player_upsert_creates_record(initbot_state):
    player = initbot_state.players.upsert(discord_id=111222333, name="alice")
    assert player.discord_id == 111222333
    assert player.name == "alice"
    assert player.id is not None
    all_players = initbot_state.players.get_all()
    assert any(p.discord_id == 111222333 for p in all_players)


def test_player_upsert_updates_name_on_second_call(initbot_state):
    initbot_state.players.upsert(discord_id=111222333, name="alice")
    initbot_state.players.upsert(discord_id=111222333, name="alice_renamed")
    all_players = initbot_state.players.get_all()
    matching = [p for p in all_players if p.discord_id == 111222333]
    assert len(matching) == 1
    assert matching[0].name == "alice_renamed"


def test_player_upsert_assigns_unique_ids(initbot_state):
    p1 = initbot_state.players.upsert(discord_id=111222333, name="alice")
    p2 = initbot_state.players.upsert(discord_id=444555666, name="bob")
    assert p1.id != p2.id


def test_player_get_from_id_returns_record(initbot_state):
    player = initbot_state.players.upsert(discord_id=111222333, name="alice")
    found = initbot_state.players.get_from_id(player.id)
    assert found.discord_id == 111222333


def test_player_get_from_id_raises_for_missing_id(initbot_state):
    with pytest.raises(KeyError):
        initbot_state.players.get_from_id(99999)


def test_player_get_from_discord_id_returns_record(initbot_state):
    player = initbot_state.players.upsert(discord_id=111222333, name="alice")
    found = initbot_state.players.get_from_discord_id(111222333)
    assert found is not None
    assert found.id == player.id


def test_player_get_from_discord_id_returns_none_when_missing(initbot_state):
    assert initbot_state.players.get_from_discord_id(999888777) is None
