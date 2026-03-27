# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from initbot_core.data.character import NewCharacterData


def test_character_with_player_id_round_trips(initbot_state):
    char = initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Harold", user="alice", player_id=42)
    )
    assert char.player_id == 42
    retrieved = initbot_state.characters.get_from_name("Harold")
    assert retrieved.player_id == 42


def test_character_without_player_id_defaults_to_none(initbot_state):
    char = initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Legacy", user="alice")
    )
    assert char.player_id is None
    retrieved = initbot_state.characters.get_from_name("Legacy")
    assert retrieved.player_id is None
