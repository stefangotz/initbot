import pathlib
import shutil

import pytest

from initbot.data.character import CharacterData
from initbot.state.factory import create_state_from_source


DATA_DIR = pathlib.Path(__file__).parent / "data"
REFERENCE_FILES = [
    "abilities.json",
    "augurs.json",
    "occupations.json",
    "classes.json",
    "crits.json",
]


def test_add_character_and_retrieve(initbot_state):
    cdi = initbot_state.characters.add_store_and_get(
        CharacterData(name="Bob", user="alice")
    )
    assert cdi.name == "Bob"
    assert cdi.user == "alice"
    bobs = [c for c in initbot_state.characters.get_all() if c.name == "Bob"]
    assert len(bobs) == 1


def test_add_character_persists_on_reload(tmp_path):
    for f in REFERENCE_FILES:
        shutil.copy(DATA_DIR / f, tmp_path / f)
    state1 = create_state_from_source(f"json:{tmp_path}")
    state1.characters.add_store_and_get(CharacterData(name="Bob", user="alice"))

    state2 = create_state_from_source(f"json:{tmp_path}")
    bobs = [c for c in state2.characters.get_all() if c.name == "Bob"]
    assert len(bobs) == 1


def test_update_character_persists(initbot_state):
    cdi = initbot_state.characters.add_store_and_get(
        CharacterData(name="Bob", user="alice", strength=10)
    )
    cdi.strength = 14
    initbot_state.characters.update_and_store(cdi)
    retrieved = initbot_state.characters.get_from_name("Bob")
    assert retrieved.strength == 14


def test_remove_character(initbot_state):
    cdi = initbot_state.characters.add_store_and_get(
        CharacterData(name="Bob", user="alice")
    )
    initbot_state.characters.remove_and_store(cdi)
    remaining = [c for c in initbot_state.characters.get_all() if c.name == "Bob"]
    assert len(remaining) == 0


def test_lookup_by_prefix(initbot_state):
    initbot_state.characters.add_store_and_get(
        CharacterData(name="Mediocre Mel", user="alice")
    )
    found = initbot_state.characters.get_from_name("Med")
    assert found.name == "Mediocre Mel"
    with pytest.raises(KeyError):
        initbot_state.characters.get_from_name("Nonexistent")


def test_lookup_by_user(initbot_state):
    initbot_state.characters.add_store_and_get(
        CharacterData(name="Mediocre Mel", user="alice", active=True)
    )
    found = initbot_state.characters.get_from_user("alice")
    assert found.name == "Mediocre Mel"


def test_abilities_lookup(initbot_state):
    result = initbot_state.abilities.get_from_prefix("test")
    assert result is not None
    assert result.name == "test"


def test_augur_lookup(initbot_state):
    result = initbot_state.augurs.get_from_roll(1)
    assert result is not None


def test_occupation_lookup(initbot_state):
    result = initbot_state.occupations.get_from_roll(1)
    assert result is not None
