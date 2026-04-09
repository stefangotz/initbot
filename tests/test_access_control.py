# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import pytest

from initbot_core.data.character import NewCharacterData


def test_access_control_uses_player_id(initbot_state):
    player = initbot_state.players.upsert(discord_id=111, name="alice")
    initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Harold", player_id=player.id)
    )
    found = initbot_state.characters.get_from_tokens((), player_id=player.id)
    assert found.name == "Harold"


def test_get_from_player_id_raises_when_no_match(initbot_state):
    with pytest.raises(KeyError):
        initbot_state.characters.get_from_player_id(99999)
