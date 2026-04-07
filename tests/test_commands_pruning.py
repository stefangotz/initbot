# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import time
from unittest.mock import patch

from initbot_chat.commands.character import prune, touch, unused
from initbot_core.data.character import NewCharacterData

# Shift "now" 200 days into the future so every recently-added character
# looks old enough to be eligible for pruning.
_FUTURE = int(time.time()) + 200 * 86400

# Must match mock_ctx.author.id in conftest.py so that sync_player inside the
# commands finds the same player record created here.
_DISCORD_IDS: dict[str, int] = {
    "testuser": 100000000000000001,
    "otheruser": 200000000000000002,
}


def _add_old(state, name, user):
    """Add a character and immediately make it appear old via a patched time."""
    discord_id = _DISCORD_IDS.get(user, abs(hash(user)) % (10**15))
    player = state.players.upsert(discord_id=discord_id, name=user)
    with (
        patch("initbot_core.state.local.time") as m_local,
        patch("initbot_core.state.sql.time") as m_sql,
    ):
        m_local.time.return_value = 0
        m_sql.time.return_value = 0
        return state.characters.add_store_and_get(
            NewCharacterData(name=name, user=user, player_id=player.id)
        )


async def test_unused_own(mock_ctx):
    _add_old(mock_ctx.bot.initbot_state, "OldMel", "testuser")
    _add_old(mock_ctx.bot.initbot_state, "OldBob", "testuser")
    with patch("initbot_core.data.character.time") as mock_t:
        mock_t.time.return_value = _FUTURE
        await unused.callback(mock_ctx)
    all_msgs = " ".join(str(c) for c in mock_ctx.send.call_args_list)
    assert "OldMel" in all_msgs
    assert "OldBob" in all_msgs


async def test_unused_excludes_other_player(mock_ctx):
    _add_old(mock_ctx.bot.initbot_state, "OtherChar", "otheruser")
    with patch("initbot_core.data.character.time") as mock_t:
        mock_t.time.return_value = _FUTURE
        await unused.callback(mock_ctx)
    msg = mock_ctx.send.call_args[0][0]
    assert "OtherChar" not in msg


async def test_unused_all_players_flag(mock_ctx):
    _add_old(mock_ctx.bot.initbot_state, "MyChar", "testuser")
    _add_old(mock_ctx.bot.initbot_state, "TheirChar", "otheruser")
    with patch("initbot_core.data.character.time") as mock_t:
        mock_t.time.return_value = _FUTURE
        await unused.callback(mock_ctx, "all_players")
    all_msgs = " ".join(str(c) for c in mock_ctx.send.call_args_list)
    assert "MyChar" in all_msgs
    assert "TheirChar" in all_msgs


async def test_unused_empty(mock_ctx):
    # No characters added — state is empty
    with patch("initbot_core.data.character.time") as mock_t:
        mock_t.time.return_value = _FUTURE
        await unused.callback(mock_ctx)
    msg = mock_ctx.send.call_args[0][0]
    assert "unused" in msg


async def test_prune_removes(mock_ctx):
    _add_old(mock_ctx.bot.initbot_state, "OldMel", "testuser")
    with patch("initbot_core.data.character.time") as mock_t:
        mock_t.time.return_value = _FUTURE
        await prune.callback(mock_ctx)
    remaining = [
        c for c in mock_ctx.bot.initbot_state.characters.get_all() if c.name == "OldMel"
    ]
    assert len(remaining) == 0
    msg = mock_ctx.send.call_args[0][0]
    assert "OldMel" in msg


async def test_prune_spares_recent(mock_ctx):
    mock_ctx.bot.initbot_state.characters.add_store_and_get(
        NewCharacterData(name="RecentMel", user="testuser")
    )
    # No time patch — character was just created so last_used ≈ now → not eligible
    await prune.callback(mock_ctx)
    remaining = [
        c
        for c in mock_ctx.bot.initbot_state.characters.get_all()
        if c.name == "RecentMel"
    ]
    assert len(remaining) == 1
    msg = mock_ctx.send.call_args[0][0]
    assert "No characters" in msg


async def test_touch_single(mock_ctx):
    _add_old(mock_ctx.bot.initbot_state, "Mel", "testuser")
    before = int(time.time())
    await touch.callback(mock_ctx, "Mel")
    after = int(time.time())
    mel = mock_ctx.bot.initbot_state.characters.get_from_name("Mel")
    assert mel.last_used is not None
    assert before <= mel.last_used <= after
    msg = mock_ctx.send.call_args[0][0]
    assert "Mel" in msg


async def test_touch_multiple(mock_ctx):
    _add_old(mock_ctx.bot.initbot_state, "Mel", "testuser")
    _add_old(mock_ctx.bot.initbot_state, "Bob", "testuser")
    before = int(time.time())
    await touch.callback(mock_ctx, "Mel", "Bob")
    after = int(time.time())
    for name in ("Mel", "Bob"):
        char = mock_ctx.bot.initbot_state.characters.get_from_name(name)
        assert char.last_used is not None
        assert before <= char.last_used <= after
    all_msgs = " ".join(str(c) for c in mock_ctx.send.call_args_list)
    assert "Mel" in all_msgs
    assert "Bob" in all_msgs


async def test_touch_no_args(mock_ctx):
    mock_ctx.bot.initbot_state.characters.add_store_and_get(
        NewCharacterData(name="OnlyChar", user="testuser")
    )
    before = int(time.time())
    await touch.callback(mock_ctx)
    after = int(time.time())
    char = mock_ctx.bot.initbot_state.characters.get_from_name("OnlyChar")
    assert char.last_used is not None
    assert before <= char.last_used <= after
