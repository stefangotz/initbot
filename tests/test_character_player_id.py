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


def test_character_without_player_id_gets_placeholder_player(initbot_state):
    char = initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Legacy", user="alice")
    )
    assert char.player_id is not None
    player = initbot_state.players.get_from_id(char.player_id)
    assert player is not None
    assert player.name == "alice"
    assert player.discord_id is None  # placeholder until Discord user syncs
