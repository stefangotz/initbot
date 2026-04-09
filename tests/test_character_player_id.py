# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from initbot_core.data.character import NewCharacterData


def test_character_with_player_id_round_trips(initbot_state):
    player = initbot_state.players.upsert(discord_id=42, name="alice")
    char = initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Harold", player_id=player.id)
    )
    assert char.player_id == player.id
    retrieved = initbot_state.characters.get_from_name("Harold")
    assert retrieved.player_id == player.id
