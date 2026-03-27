# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from initbot_chat.commands.character import new, park, play
from initbot_core.data.character import NewCharacterData


async def test_new_creates_character(mock_ctx):
    await new.callback(mock_ctx, "Newchar")
    characters = list(mock_ctx.bot.initbot_state.characters.get_all())
    names = [c.name for c in characters]
    assert "Newchar" in names
    newchar = next(c for c in characters if c.name == "Newchar")
    # Ability scores are rolled 3d6 so must be in 3-18
    for attr in ("strength", "agility", "stamina", "personality", "intelligence"):
        val = getattr(newchar, attr)
        assert isinstance(val, int), f"{attr} should be an int"
        assert 3 <= val <= 18, f"{attr}={val} out of range"
    assert isinstance(newchar.luck, int)
    assert newchar.occupation is not None


async def test_park_deactivates_character(mock_ctx):
    mock_ctx.bot.initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Mel", user="testuser")
    )
    await park.callback(mock_ctx, "Mel")
    mel = mock_ctx.bot.initbot_state.characters.get_from_name("Mel")
    assert mel.active is False


async def test_play_reactivates_character(mock_ctx):
    cdi = NewCharacterData(name="Mel", user="testuser")
    mock_ctx.bot.initbot_state.characters.add_store_and_get(cdi)
    await park.callback(mock_ctx, "Mel")
    await play.callback(mock_ctx, "Mel")
    mel = mock_ctx.bot.initbot_state.characters.get_from_name("Mel")
    assert mel.active is True


async def test_park_play_round_trip(mock_ctx):
    mock_ctx.bot.initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Mel", user="testuser")
    )
    assert mock_ctx.bot.initbot_state.characters.get_from_name("Mel").active is True

    await park.callback(mock_ctx, "Mel")
    assert mock_ctx.bot.initbot_state.characters.get_from_name("Mel").active is False

    await play.callback(mock_ctx, "Mel")
    assert mock_ctx.bot.initbot_state.characters.get_from_name("Mel").active is True
