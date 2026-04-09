# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import shutil
import sqlite3
import time

import pytest

from initbot_core.config import CORE_CFG
from initbot_core.data.character import NewCharacterData
from initbot_core.state.factory import create_state_from_source
from tests.helpers import DATA_DIR, REFERENCE_FILES


def test_add_character_and_retrieve(initbot_state):
    player = initbot_state.players.upsert(discord_id=1, name="alice")
    cdi = initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Bob", player_id=player.id)
    )
    assert cdi.name == "Bob"
    bobs = [c for c in initbot_state.characters.get_all() if c.name == "Bob"]
    assert len(bobs) == 1


def test_add_character_persists_on_reload(tmp_path):
    for f in REFERENCE_FILES:
        if (DATA_DIR / f).exists():
            shutil.copy(DATA_DIR / f, tmp_path / f)
    state1 = create_state_from_source(f"json:{tmp_path}")
    player = state1.players.upsert(discord_id=1, name="alice")
    state1.characters.add_store_and_get(
        NewCharacterData(name="Bob", player_id=player.id)
    )

    state2 = create_state_from_source(f"json:{tmp_path}")
    bobs = [c for c in state2.characters.get_all() if c.name == "Bob"]
    assert len(bobs) == 1


def test_update_character_persists(initbot_state):
    player = initbot_state.players.upsert(discord_id=1, name="alice")
    cdi = initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Bob", player_id=player.id, initiative_dice="d20+2")
    )
    cdi.initiative_dice = "d20+5"
    initbot_state.characters.update_and_store(cdi)
    retrieved = initbot_state.characters.get_from_name("Bob")
    assert retrieved.initiative_dice == "d20+5"


def test_remove_character(initbot_state):
    player = initbot_state.players.upsert(discord_id=1, name="alice")
    cdi = initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Bob", player_id=player.id)
    )
    initbot_state.characters.remove_and_store(cdi)
    remaining = [c for c in initbot_state.characters.get_all() if c.name == "Bob"]
    assert len(remaining) == 0


def test_lookup_by_prefix(initbot_state):
    player = initbot_state.players.upsert(discord_id=1, name="alice")
    initbot_state.characters.add_store_and_get(
        NewCharacterData(name="Mediocre Mel", player_id=player.id)
    )
    found = initbot_state.characters.get_from_name("Med")
    assert found.name == "Mediocre Mel"
    with pytest.raises(KeyError):
        initbot_state.characters.get_from_name("Nonexistent")


def test_update_sets_last_used(initbot_state):
    player = initbot_state.players.upsert(discord_id=1, name="alice")
    before = int(time.time())
    cdi = initbot_state.characters.add_store_and_get(
        NewCharacterData(name="TimestampChar", player_id=player.id)
    )
    cdi.initiative_dice = "d20"
    cdi.last_used = int(time.time())
    initbot_state.characters.update_and_store(cdi)
    after = int(time.time())
    assert cdi.last_used is not None
    assert before <= cdi.last_used <= after


def test_add_sets_last_used(initbot_state):
    player = initbot_state.players.upsert(discord_id=1, name="alice")
    before = int(time.time())
    cdi = initbot_state.characters.add_store_and_get(
        NewCharacterData(name="NewChar", player_id=player.id)
    )
    after = int(time.time())
    assert cdi.last_used is not None
    assert before <= cdi.last_used <= after


def test_legacy_creation_time_migration_json(tmp_path):
    for f in REFERENCE_FILES:
        if (DATA_DIR / f).exists():
            shutil.copy(DATA_DIR / f, tmp_path / f)
    shutil.copy(DATA_DIR / "characters_legacy.json", tmp_path / "characters.json")

    state = create_state_from_source(f"json:{tmp_path}")
    chars = [c for c in state.characters.get_all() if c.name == "OldChar"]
    assert len(chars) == 1
    expected_ts = int(time.time()) - CORE_CFG.prune_threshold_days * 86400 // 2
    assert chars[0].last_used is not None
    assert abs(chars[0].last_used - expected_ts) < 5


def test_legacy_creation_time_migration_sqlite(tmp_path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE _sqlcharacterdata "
        "(name TEXT PRIMARY KEY, user TEXT, active INTEGER DEFAULT 1, level INTEGER DEFAULT 0, "
        "strength INTEGER, agility INTEGER, stamina INTEGER, personality INTEGER, "
        "intelligence INTEGER, luck INTEGER, initial_luck INTEGER, hit_points INTEGER, "
        "equipment TEXT, occupation INTEGER, exp INTEGER, alignment TEXT, "
        "initiative INTEGER, initiative_time INTEGER, initiative_modifier INTEGER, "
        "hit_die INTEGER, augur INTEGER, cls TEXT, creation_time INTEGER);"
    )
    conn.execute(
        "INSERT INTO _sqlcharacterdata (name, user, creation_time) VALUES ('LegacyChar', 'bob', 1000000);"
    )
    conn.commit()
    conn.close()

    state = create_state_from_source(f"sqlite:{db_path}")
    chars = [c for c in state.characters.get_all() if c.name == "LegacyChar"]
    assert len(chars) == 1
    expected_ts = int(time.time()) - CORE_CFG.prune_threshold_days * 86400 // 2
    assert chars[0].last_used is not None
    assert abs(chars[0].last_used - expected_ts) < 5
