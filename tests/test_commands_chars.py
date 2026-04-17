# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import pytest
from discord.ext import commands

from initbot_chat.commands.character import (
    char,
    char_error,
    chars,
    init_dice,
    remove,
    rename,
)
from initbot_core.data.character import NewCharacterData


async def test_chars_empty_state(mock_ctx):
    await chars.callback(mock_ctx)
    # With empty state send_in_parts produces no output — just verify no crash


async def test_chars_with_character(mock_ctx):
    mock_ctx.bot.initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Mel", player_id=mock_ctx.author.player_id)
    )
    await chars.callback(mock_ctx)
    mock_ctx.send.assert_called()
    all_msgs = " ".join(str(call) for call in mock_ctx.send.call_args_list)
    assert "Mel" in all_msgs


async def test_char_by_prefix(mock_ctx):
    mock_ctx.bot.initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Mediocre Mel", player_id=mock_ctx.author.player_id)
    )
    await char.callback(mock_ctx, "Med")
    mock_ctx.send.assert_called()
    msg = mock_ctx.send.call_args[0][0]
    assert "Mediocre Mel" in msg


async def test_char_missing_sends_error(mock_ctx):
    try:
        await char.callback(mock_ctx, "Nonexistent")
    except KeyError as exc:
        await char_error(mock_ctx, commands.CommandError(str(exc)))  # type: ignore[missing-argument]  # discord.py stubs type error handlers as (self, ctx, error) | (ctx, error)
    mock_ctx.send.assert_called()


async def test_remove_character(mock_ctx):
    mock_ctx.bot.initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Mel", player_id=mock_ctx.author.player_id)
    )
    await remove.callback(mock_ctx, "Mel")
    mock_ctx.send.assert_called()
    msg = mock_ctx.send.call_args[0][0]
    assert "Mel" in msg
    remaining = [
        c for c in mock_ctx.bot.initbot_state.characters.get_all() if c.name == "Mel"
    ]
    assert len(remaining) == 0


async def test_duplicate_name_case_insensitive_rejected(mock_ctx):
    mock_ctx.bot.initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Foo", player_id=mock_ctx.author.player_id)
    )
    with pytest.raises(ValueError, match="Foo"):
        mock_ctx.bot.initbot_state.characters.add_store_and_get(
            NewCharacterData(name="foo", player_id=mock_ctx.author.player_id)
        )


async def test_duplicate_name_exact_rejected(mock_ctx):
    mock_ctx.bot.initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Foo", player_id=mock_ctx.author.player_id)
    )
    with pytest.raises(ValueError, match="Foo"):
        mock_ctx.bot.initbot_state.characters.add_store_and_get(
            NewCharacterData(name="Foo", player_id=mock_ctx.author.player_id)
        )


async def test_rename_single_character(mock_ctx):
    mock_ctx.bot.initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Mel", player_id=mock_ctx.author.player_id)
    )
    await rename.callback(mock_ctx, "Zara")
    mock_ctx.send.assert_called()
    msg = mock_ctx.send.call_args[0][0]
    assert "Zara" in msg
    names = [c.name for c in mock_ctx.bot.initbot_state.characters.get_all()]
    assert "Zara" in names
    assert "Mel" not in names


async def test_rename_by_exact_name(mock_ctx):
    mock_ctx.bot.initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Alpha", player_id=mock_ctx.author.player_id)
    )
    mock_ctx.bot.initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Beta", player_id=mock_ctx.author.player_id)
    )
    await rename.callback(mock_ctx, "Alpha", "Gamma")
    names = [c.name for c in mock_ctx.bot.initbot_state.characters.get_all()]
    assert "Gamma" in names
    assert "Alpha" not in names
    assert "Beta" in names


async def test_rename_by_prefix(mock_ctx):
    mock_ctx.bot.initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Mediocre Mel", player_id=mock_ctx.author.player_id)
    )
    await rename.callback(mock_ctx, "Med", "Zara")
    names = [c.name for c in mock_ctx.bot.initbot_state.characters.get_all()]
    assert "Zara" in names
    assert "Mediocre Mel" not in names


async def test_rename_conflict_rejected(mock_ctx):
    mock_ctx.bot.initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Alpha", player_id=mock_ctx.author.player_id)
    )
    mock_ctx.bot.initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Beta", player_id=mock_ctx.author.player_id)
    )
    with pytest.raises(ValueError, match="Beta"):
        await rename.callback(mock_ctx, "Alpha", "Beta")


async def test_rename_conflict_case_insensitive(mock_ctx):
    mock_ctx.bot.initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Alpha", player_id=mock_ctx.author.player_id)
    )
    mock_ctx.bot.initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Beta", player_id=mock_ctx.author.player_id)
    )
    with pytest.raises(ValueError, match="Beta"):
        await rename.callback(mock_ctx, "Alpha", "beta")


async def test_init_dice_sets_spec_preserves_initiative(mock_ctx):
    mock_ctx.bot.initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Mel", player_id=mock_ctx.author.player_id, initiative=14)
    )
    await init_dice.callback(mock_ctx, "d20+3")
    updated = mock_ctx.bot.initbot_state.characters.get_from_name("Mel")
    assert updated.initiative_dice == "d20+3"
    assert updated.initiative == 14


async def test_rename_preserves_actions(mock_ctx):
    cdi = mock_ctx.bot.initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Mel", player_id=mock_ctx.author.player_id)
    )
    mock_ctx.bot.initbot_state.character_actions.add(cdi.name, "Stab {target}")
    await rename.callback(mock_ctx, "Zara")
    actions = mock_ctx.bot.initbot_state.character_actions.get_all_for_character("Zara")
    assert list(actions) == ["Stab {target}"]
