# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import pytest

from initbot_core.data.character import CharacterData


def test_access_control_uses_player_id(initbot_state):
    player = initbot_state.players.upsert(discord_id=111, name="alice")
    initbot_state.characters.add_store_and_get(
        CharacterData(name="Harold", user="alice", player_id=player.id)
    )
    found = initbot_state.characters.get_from_tokens((), "alice", player_id=player.id)
    assert found.name == "Harold"


def test_access_control_falls_back_for_legacy_characters(initbot_state):
    initbot_state.characters.add_store_and_get(
        CharacterData(name="Harold", user="alice")
    )
    found = initbot_state.characters.get_from_tokens((), "alice")
    assert found.name == "Harold"


def test_access_control_player_id_takes_precedence_over_user(initbot_state):
    player = initbot_state.players.upsert(discord_id=111, name="alice_new")
    initbot_state.characters.add_store_and_get(
        CharacterData(name="Harold", user="alice_old", player_id=player.id)
    )
    found = initbot_state.characters.get_from_tokens(
        (), "alice_new", player_id=player.id
    )
    assert found.name == "Harold"


def test_get_from_player_id_raises_when_no_match(initbot_state):
    with pytest.raises(KeyError):
        initbot_state.characters.get_from_player_id(99999)
