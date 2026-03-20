# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from initbot_chat.commands.character import char, char_error, chars, remove, set_
from initbot_core.data.character import CharacterData


async def test_chars_empty_state(mock_ctx):
    await chars.callback(mock_ctx)
    # With empty state send_in_parts produces no output — just verify no crash


async def test_chars_with_character(mock_ctx):
    mock_ctx.bot.initbot_state.characters.add_store_and_get(
        CharacterData(name="Mel", user="testuser")
    )
    await chars.callback(mock_ctx)
    mock_ctx.send.assert_called()
    all_msgs = " ".join(str(call) for call in mock_ctx.send.call_args_list)
    assert "Mel" in all_msgs


async def test_char_by_prefix(mock_ctx):
    mock_ctx.bot.initbot_state.characters.add_store_and_get(
        CharacterData(name="Mediocre Mel", user="testuser")
    )
    await char.callback(mock_ctx, "Med")
    mock_ctx.send.assert_called()
    msg = mock_ctx.send.call_args[0][0]
    assert "Mediocre Mel" in msg


async def test_char_missing_sends_error(mock_ctx):
    try:
        await char.callback(mock_ctx, "Nonexistent")
    except KeyError as exc:
        await char_error(mock_ctx, exc)
    mock_ctx.send.assert_called()


async def test_remove_character(mock_ctx):
    mock_ctx.bot.initbot_state.characters.add_store_and_get(
        CharacterData(name="Mel", user="testuser")
    )
    await remove.callback(mock_ctx, "Mel")
    mock_ctx.send.assert_called()
    msg = mock_ctx.send.call_args[0][0]
    assert "Mel" in msg
    remaining = [
        c for c in mock_ctx.bot.initbot_state.characters.get_all() if c.name == "Mel"
    ]
    assert len(remaining) == 0


async def test_set_attribute(mock_ctx):
    mock_ctx.bot.initbot_state.characters.add_store_and_get(
        CharacterData(name="Mel", user="testuser")
    )
    await set_.callback(mock_ctx, txt="Mel strength 14")
    mock_ctx.send.assert_called()
    msg = mock_ctx.send.call_args[0][0]
    assert "strength" in msg
    assert "14" in msg
    mel = mock_ctx.bot.initbot_state.characters.get_from_name("Mel")
    assert mel.strength == 14
