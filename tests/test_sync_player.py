# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from unittest.mock import MagicMock

from initbot_chat.commands.utils import player_name, sync_player
from initbot_core.data.character import NewCharacterData


def _make_ctx(discord_id: int = 111222333, name: str = "alice"):
    ctx = MagicMock()
    ctx.author.id = discord_id
    ctx.author.name = name
    return ctx


def test_sync_player_creates_player_record(initbot_state):
    ctx = _make_ctx()
    player = sync_player(initbot_state, ctx)
    assert player.discord_id == 111222333
    assert player.name == "alice"
    assert initbot_state.players.get_from_discord_id(111222333) is not None


def test_sync_player_updates_name_on_second_call(initbot_state):
    ctx = _make_ctx()
    sync_player(initbot_state, ctx)
    ctx2 = _make_ctx(name="alice_renamed")
    player = sync_player(initbot_state, ctx2)
    assert player.name == "alice_renamed"
    assert player.discord_id == 111222333


def test_sync_player_does_not_overwrite_existing_player_id(initbot_state):
    other_player = initbot_state.players.upsert(discord_id=999, name="other")
    initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Harold", player_id=other_player.id)
    )

    ctx = _make_ctx()
    sync_player(initbot_state, ctx)

    updated = initbot_state.characters.get_from_name("Harold")
    assert updated.player_id == other_player.id


def test_character_display_uses_player_name_when_available(initbot_state):
    player = initbot_state.players.upsert(discord_id=111222333, name="alice_display")
    char = initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Harold", player_id=player.id)
    )
    assert player_name(initbot_state, char) == "alice_display"
