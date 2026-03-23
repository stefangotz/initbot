# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
import time
from collections.abc import Mapping, MutableSequence, Sequence, Set
from dataclasses import asdict
from pathlib import Path
from typing import Any, Final, cast

from pydantic import BaseModel, ConfigDict

from initbot_core.config import CORE_CFG
from initbot_core.data.ability import AbilityData, AbilityModifierData
from initbot_core.data.augur import AugurData
from initbot_core.data.character import CharacterData
from initbot_core.data.cls import ClassData
from initbot_core.data.crit import CritTableData
from initbot_core.data.occupation import OccupationData
from initbot_core.state.state import (
    AbilityState,
    AugurState,
    CharacterState,
    ClassState,
    CritState,
    OccupationState,
    State,
)


class LocalBaseModel(BaseModel):
    def as_dict(self) -> Mapping[str, Any]:
        return self.model_dump()


class LocalAbilityData(LocalBaseModel):
    model_config = ConfigDict(frozen=True)
    name: str
    description: str


class LocalAbilityModifierData(LocalBaseModel):
    model_config = ConfigDict(frozen=True)
    score: int
    mod: int
    spells: int
    max_spell_level: int


class LocalAbilitiesData(LocalBaseModel):
    model_config = ConfigDict(frozen=True)
    abilities: tuple[LocalAbilityData, ...] = ()
    modifiers: tuple[LocalAbilityModifierData, ...] = ()


class LocalAbilityState(AbilityState):
    def __init__(self, source_dir: Path):
        self._abilities_data = LocalAbilitiesData()
        path: Final[Path] = source_dir / "abilities.json"
        if path.exists():
            with path.open() as file_desc:
                self._abilities_data = LocalAbilitiesData.model_validate_json(
                    file_desc.read()
                )
        else:
            logging.info("No ability data loaded from %s", path)

    def get_all(self) -> Sequence[AbilityData]:
        return cast(Sequence[AbilityData], self._abilities_data.abilities)

    def get_mods(self) -> Sequence[AbilityModifierData]:
        return cast(Sequence[AbilityModifierData], self._abilities_data.modifiers)

    def import_from(self, src: AbilityState) -> None:
        raise NotImplementedError()


class LocalAugurData(LocalBaseModel):
    model_config = ConfigDict(frozen=True)
    description: str
    roll: int


class LocalAugursData(LocalBaseModel):
    model_config = ConfigDict(frozen=True)
    augurs: tuple[LocalAugurData, ...] = ()


class LocalAugurState(AugurState):
    def __init__(self, source_dir: Path):
        augurs_data = LocalAugursData()
        path: Final[Path] = source_dir / "augurs.json"
        if path.exists():
            with path.open() as file_desc:
                augurs_data = LocalAugursData.model_validate_json(file_desc.read())
        else:
            logging.info("No augur data loaded from %s", path)

        self._augurs_dict: Mapping[int, LocalAugurData] = {
            aug.roll: aug for aug in augurs_data.augurs
        }

    def get_all(self) -> Sequence[AugurData]:
        return cast(Sequence[AugurData], tuple(self._augurs_dict.values()))

    def get_from_roll(self, roll: int) -> AugurData:
        return cast(AugurData, self._augurs_dict[roll])

    def import_from(self, src: AugurState) -> None:
        raise NotImplementedError()


class LocalCharacterData(LocalBaseModel):
    name: str
    user: str
    active: bool = True
    level: int = 0
    strength: int | None = None
    agility: int | None = None
    stamina: int | None = None
    personality: int | None = None
    intelligence: int | None = None
    luck: int | None = None
    initial_luck: int | None = None
    hit_points: int | None = None
    equipment: Sequence[str] | None = None
    occupation: int | None = None
    exp: int | None = None
    alignment: str | None = None
    initiative: int | None = None
    initiative_time: int | None = None
    initiative_modifier: int | None = None
    hit_die: int | None = None
    augur: int | None = None
    cls: str | None = None
    last_used: int | None = None


class LocalCharactersData(LocalBaseModel):
    characters: MutableSequence[LocalCharacterData] = []


class LocalCharacterState(CharacterState):
    def __init__(self, source_dir: Path):
        chars_data = LocalCharactersData()
        self._path: Final[Path] = source_dir / "characters.json"
        if self._path.exists():
            with self._path.open() as file_desc:
                chars_data = LocalCharactersData.model_validate_json(file_desc.read())
        else:
            logging.info("No augur data loaded from {self._path}")

        self._characters: MutableSequence[LocalCharacterData] = chars_data.characters

        # Remove this migration once we can assume that all character data has a last_used timestamp. This is needed to prevent characters from being pruned immediately after the update.
        grace_ts = int(time.time()) - CORE_CFG.prune_threshold_days * 86400 // 2
        migrated = False
        for char in self._characters:
            if char.last_used is None:
                char.last_used = grace_ts
                migrated = True
        if migrated:
            self._store()

    def get_all(self) -> Sequence[CharacterData]:
        return cast(Sequence[CharacterData], self._characters)

    def add_store_and_get(self, char_data: CharacterData) -> CharacterData:
        if any(char for char in self.get_all() if char.name == char_data.name):
            raise KeyError(f"Character with name '{char_data.name}' already exists")
        local_char_data = LocalCharacterData(**asdict(char_data))
        local_char_data.last_used = int(time.time())
        self._characters.append(local_char_data)
        self._store()
        return cast(CharacterData, local_char_data)

    def remove_and_store(self, char_data: CharacterData) -> None:
        if not isinstance(char_data, LocalCharacterData):
            raise TypeError(
                f"Only character data returned by the State class can be removed: {char_data}"
            )
        self._characters.remove(cast(LocalCharacterData, char_data))
        self._store()

    def update_and_store(self, char_data: CharacterData) -> None:
        if not isinstance(char_data, LocalCharacterData):
            raise TypeError(
                f"Only character data returned by the State class can be updated: {char_data}"
            )
        if char_data not in self._characters:
            raise ValueError(
                f"Character data is not present in the data store yet; this is not supported: {char_data}"
            )
        char_data.last_used = int(time.time())
        self._store()

    def _store(self) -> None:
        with open(self._path, "w", encoding="UTF8") as file_desc:
            file_desc.write(
                LocalCharactersData(characters=self._characters).model_dump_json()
            )

    def import_from(self, src: CharacterState) -> None:
        raise NotImplementedError()


class LocalOccupationData(LocalBaseModel):
    model_config = ConfigDict(frozen=True)
    rolls: tuple[int, ...]
    name: str
    weapon: str
    goods: str


class LocalOccupationsData(LocalBaseModel):
    model_config = ConfigDict(frozen=True)
    occupations: tuple[LocalOccupationData, ...] = ()


class LocalOccupationState(OccupationState):
    def __init__(self, source_dir: Path):
        occupations_data: LocalOccupationsData = LocalOccupationsData()
        path: Final[Path] = source_dir / "occupations.json"
        if path.exists():
            with path.open() as file_desc:
                occupations_data = LocalOccupationsData.model_validate_json(
                    file_desc.read()
                )
        else:
            logging.info("No occupation data loaded from %s", path)
        self._occupations: Sequence[LocalOccupationData] = occupations_data.occupations

    def get_all(self) -> Sequence[OccupationData]:
        return cast(Sequence[OccupationData], self._occupations)

    def import_from(self, src: OccupationState) -> None:
        raise NotImplementedError()


class LocalSpellsByLevelData(LocalBaseModel):
    model_config = ConfigDict(frozen=True)
    level: int
    spells: int


# pylint: disable=R0801
class LocalLevelData(LocalBaseModel):
    model_config = ConfigDict(frozen=True)
    level: int
    attack_die: str
    crit_die: str
    crit_table: int
    action_dice: tuple[str, ...]
    ref: int
    fort: int
    will: int
    spells_by_level: tuple[LocalSpellsByLevelData, ...]
    thief_luck_die: int
    threat_range: tuple[int, ...]
    spells: int
    max_spell_level: int
    sneak_hide: int


class LocalClassData(LocalBaseModel):
    model_config = ConfigDict(frozen=True)
    name: str
    hit_die: int
    weapons: tuple[str, ...]
    levels: tuple[LocalLevelData, ...]


class LocalClassesData(LocalBaseModel):
    model_config = ConfigDict(frozen=True)
    classes: tuple[LocalClassData, ...] = ()


class LocalClassState(ClassState):
    def __init__(self, source_dir: Path):
        classes_data: LocalClassesData = LocalClassesData()
        path: Final[Path] = source_dir / "classes.json"
        if path.exists():
            with path.open() as file_desc:
                classes_data = LocalClassesData.model_validate_json(file_desc.read())
        else:
            logging.info("No class data loaded from %s", path)
        self._classes: Sequence[LocalClassData] = classes_data.classes

    def get_all(self) -> Sequence[ClassData]:
        return cast(Sequence[ClassData], tuple(self._classes))

    def import_from(self, src: ClassState) -> None:
        raise NotImplementedError()


class LocalCritData(LocalBaseModel):
    model_config = ConfigDict(frozen=True)
    rolls: tuple[int, ...]
    effect: str


class LocalCritTableData(LocalBaseModel):
    model_config = ConfigDict(frozen=True)
    number: int
    crits: tuple[LocalCritData, ...]


class LocalCritTablesData(LocalBaseModel):
    model_config = ConfigDict(frozen=True)
    crit_tables: tuple[LocalCritTableData, ...] = ()


class LocalCritState(CritState):
    def __init__(self, source_dir: Path):
        data: LocalCritTablesData = LocalCritTablesData()
        path: Final[Path] = source_dir / "crits.json"
        if path.exists():
            with path.open() as file_desc:
                data = LocalCritTablesData.model_validate_json(file_desc.read())
        else:
            logging.info("No crit data loaded from %s", path)
        self._data: Sequence[LocalCritTableData] = data.crit_tables

    def get_all(self) -> Sequence[CritTableData]:
        return cast(Sequence[CritTableData], self._data)

    def import_from(self, src: CritState) -> None:
        raise NotImplementedError()


class LocalState(State):
    def __init__(self, source: str):
        source_dir = Path(source.split(":", maxsplit=1)[-1])
        if not source_dir.exists():
            raise ValueError(
                f"Source directory {source_dir} does not exist. Please provide a valid path for bot state."
            )
        self._abilities = LocalAbilityState(source_dir)
        self._augurs = LocalAugurState(source_dir)
        self._characters = LocalCharacterState(source_dir)
        self._occupations = LocalOccupationState(source_dir)
        self._classes = LocalClassState(source_dir)
        self._crits = LocalCritState(source_dir)

    @property
    def abilities(self) -> AbilityState:
        return self._abilities

    @property
    def augurs(self) -> AugurState:
        return self._augurs

    @property
    def characters(self) -> CharacterState:
        return self._characters

    @property
    def occupations(self) -> OccupationState:
        return self._occupations

    @property
    def classes(self) -> ClassState:
        return self._classes

    @property
    def crits(self) -> CritState:
        return self._crits

    @classmethod
    def get_supported_state_types(cls) -> Set[str]:
        return {"json"}
