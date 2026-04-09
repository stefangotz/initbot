# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import pytest

from initbot_chat.commands.actions import act_cmd, actions_cmd
from initbot_chat.commands.character import prune, remove
from initbot_core.data.character import NewCharacterData
from initbot_core.models.roll import contains_dice_rolls


def _add_char(mock_ctx, name="Mel"):
    return mock_ctx.bot.initbot_state.characters.add_store_and_get(
        NewCharacterData(name=name, player_id=mock_ctx.author.player_id)
    )


# ---------------------------------------------------------------------------
# $actions list
# ---------------------------------------------------------------------------


async def test_actions_list_empty(mock_ctx):
    _add_char(mock_ctx)
    await actions_cmd.callback(mock_ctx, "list")
    mock_ctx.send.assert_called()
    msg = mock_ctx.send.call_args[0][0]
    assert "no actions" in msg


async def test_actions_list_shows_templates(mock_ctx):
    _add_char(mock_ctx)
    mock_ctx.bot.initbot_state.character_actions.add("Mel", "Mel attacks at d20+3")
    mock_ctx.bot.initbot_state.character_actions.add("Mel", "Mel charges at d20+5")
    await actions_cmd.callback(mock_ctx, "list")
    mock_ctx.send.assert_called()
    all_msgs = " ".join(str(call) for call in mock_ctx.send.call_args_list)
    assert "d20+3" in all_msgs
    assert "d20+5" in all_msgs
    assert "1." in all_msgs
    assert "2." in all_msgs


# ---------------------------------------------------------------------------
# $actions add
# ---------------------------------------------------------------------------


async def test_actions_add_and_list(mock_ctx):
    _add_char(mock_ctx)
    await actions_cmd.callback(
        mock_ctx, "add", "Mel", "attacks", "with", "axe", "at", "d20+3", "for", "2d6"
    )
    mock_ctx.send.assert_called()
    msg = mock_ctx.send.call_args[0][0]
    assert "#1" in msg
    assert "Mel" in msg

    templates = mock_ctx.bot.initbot_state.character_actions.get_all_for_character(
        "Mel"
    )
    assert len(templates) == 1
    assert "d20+3" in templates[0]


async def test_actions_add_validates_dice_roll(mock_ctx):
    _add_char(mock_ctx)
    with pytest.raises(ValueError, match="dice roll"):
        await actions_cmd.callback(mock_ctx, "add", "just", "plain", "text")


async def test_actions_add_no_template_raises(mock_ctx):
    _add_char(mock_ctx)
    with pytest.raises(ValueError, match="template"):
        await actions_cmd.callback(mock_ctx, "add")


# ---------------------------------------------------------------------------
# $actions update
# ---------------------------------------------------------------------------


async def test_actions_update(mock_ctx):
    _add_char(mock_ctx)
    mock_ctx.bot.initbot_state.character_actions.add("Mel", "Mel attacks at d20+3")
    await actions_cmd.callback(mock_ctx, "update", "1", "Mel", "swings", "at", "d20+5")
    templates = mock_ctx.bot.initbot_state.character_actions.get_all_for_character(
        "Mel"
    )
    assert len(templates) == 1
    assert "d20+5" in templates[0]
    assert "d20+3" not in templates[0]


async def test_actions_update_out_of_range(mock_ctx):
    _add_char(mock_ctx)
    mock_ctx.bot.initbot_state.character_actions.add("Mel", "Mel attacks at d20+3")
    with pytest.raises(IndexError):
        await actions_cmd.callback(
            mock_ctx, "update", "99", "Mel", "swings", "at", "d20+5"
        )


async def test_actions_update_validates_dice_roll(mock_ctx):
    _add_char(mock_ctx)
    mock_ctx.bot.initbot_state.character_actions.add("Mel", "Mel attacks at d20+3")
    with pytest.raises(ValueError, match="dice roll"):
        await actions_cmd.callback(mock_ctx, "update", "1", "no", "dice", "here")


# ---------------------------------------------------------------------------
# $actions remove
# ---------------------------------------------------------------------------


async def test_actions_remove_and_renumber(mock_ctx):
    _add_char(mock_ctx)
    mock_ctx.bot.initbot_state.character_actions.add("Mel", "Mel attacks at d20+3")
    mock_ctx.bot.initbot_state.character_actions.add("Mel", "Mel charges at d20+5")
    await actions_cmd.callback(mock_ctx, "remove", "1")
    msg = mock_ctx.send.call_args[0][0]
    assert "d20+3" in msg
    templates = mock_ctx.bot.initbot_state.character_actions.get_all_for_character(
        "Mel"
    )
    assert len(templates) == 1
    assert "d20+5" in templates[0]


async def test_actions_remove_out_of_range(mock_ctx):
    _add_char(mock_ctx)
    mock_ctx.bot.initbot_state.character_actions.add("Mel", "Mel attacks at d20+3")
    await actions_cmd.callback(mock_ctx, "remove", "99")
    msg = mock_ctx.send.call_args[0][0]
    assert "only has 1 action" in msg


# ---------------------------------------------------------------------------
# $act
# ---------------------------------------------------------------------------


async def test_act_executes_template(mock_ctx):
    _add_char(mock_ctx)
    mock_ctx.bot.initbot_state.character_actions.add("Mel", "Mel attacks at d20+3")
    await act_cmd.callback(mock_ctx, "1")
    mock_ctx.send.assert_called()
    result = mock_ctx.send.call_args[0][0]
    # Dice specs should have been replaced — no raw dice in the output
    assert not contains_dice_rolls(result)
    assert "Mel attacks at" in result


async def test_act_index_out_of_range(mock_ctx):
    _add_char(mock_ctx)
    mock_ctx.bot.initbot_state.character_actions.add("Mel", "Mel attacks at d20+3")
    with pytest.raises(ValueError, match="out of range"):
        await act_cmd.callback(mock_ctx, "2")


async def test_act_no_args_lists_actions(mock_ctx):
    _add_char(mock_ctx)
    mock_ctx.bot.initbot_state.character_actions.add("Mel", "Mel attacks at d20+3")
    await act_cmd.callback(mock_ctx)
    mock_ctx.send.assert_called()
    all_msgs = " ".join(str(call) for call in mock_ctx.send.call_args_list)
    assert "d20+3" in all_msgs


async def test_act_char_prefix_no_nr_lists_actions(mock_ctx):
    _add_char(mock_ctx, name="Mediocre Mel")
    mock_ctx.bot.initbot_state.character_actions.add(
        "Mediocre Mel", "Mediocre Mel attacks at d20+1"
    )
    await act_cmd.callback(mock_ctx, "Med")
    mock_ctx.send.assert_called()
    all_msgs = " ".join(str(call) for call in mock_ctx.send.call_args_list)
    assert "d20+1" in all_msgs


async def test_act_with_character_prefix(mock_ctx):
    _add_char(mock_ctx, name="Mediocre Mel")
    mock_ctx.bot.initbot_state.character_actions.add(
        "Mediocre Mel", "Mediocre Mel attacks at d20+1"
    )
    await act_cmd.callback(mock_ctx, "Med", "1")
    mock_ctx.send.assert_called()
    result = mock_ctx.send.call_args[0][0]
    assert "Mediocre Mel attacks at" in result


# ---------------------------------------------------------------------------
# Subcommand parsing
# ---------------------------------------------------------------------------


async def test_actions_no_subcommand(mock_ctx):
    _add_char(mock_ctx)
    with pytest.raises(ValueError, match="Usage"):
        await actions_cmd.callback(mock_ctx, "Mel", "foo")


async def test_actions_with_character_prefix(mock_ctx):
    _add_char(mock_ctx, name="Mediocre Mel")
    mock_ctx.bot.initbot_state.character_actions.add(
        "Mediocre Mel", "Mediocre Mel attacks at d20+3"
    )
    await actions_cmd.callback(mock_ctx, "Med", "list")
    mock_ctx.send.assert_called()
    all_msgs = " ".join(str(call) for call in mock_ctx.send.call_args_list)
    assert "d20+3" in all_msgs


# ---------------------------------------------------------------------------
# Cascade on character delete / prune
# ---------------------------------------------------------------------------


async def test_remove_char_cascades_actions(mock_ctx):
    _add_char(mock_ctx)
    mock_ctx.bot.initbot_state.character_actions.add("Mel", "Mel attacks at d20+3")
    await remove.callback(mock_ctx, "Mel")
    # Character is gone — create a new one to verify actions were cleared
    mock_ctx.bot.initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Mel", player_id=mock_ctx.author.player_id)
    )
    templates = mock_ctx.bot.initbot_state.character_actions.get_all_for_character(
        "Mel"
    )
    assert templates == []


async def test_prune_cascades_actions(mock_ctx):
    # Create a character eligible for pruning (last_used = 0 → far in the past)
    mock_ctx.bot.initbot_state.characters.add_store_and_get(
        NewCharacterData(
            name="OldChar",
            player_id=mock_ctx.author.player_id,
            last_used=0,
        )
    )
    mock_ctx.bot.initbot_state.character_actions.add(
        "OldChar", "OldChar attacks at d20"
    )
    await prune.callback(mock_ctx)
    # Character should be pruned; re-add to check actions are gone
    mock_ctx.bot.initbot_state.characters.add_store_and_get(
        NewCharacterData(name="OldChar", player_id=mock_ctx.author.player_id)
    )
    templates = mock_ctx.bot.initbot_state.character_actions.get_all_for_character(
        "OldChar"
    )
    assert templates == []
