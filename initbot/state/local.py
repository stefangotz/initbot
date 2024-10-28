from dataclasses import asdict
import logging
from pathlib import Path
from typing import Dict, Iterable, List, Union, cast

from pydantic import BaseModel, ConfigDict

from initbot.data.cls import ClassData
from initbot.data.crit import CritTableData

from ..data.ability import AbilityData, AbilityModifierData
from ..data.augur import AugurData
from ..data.character import CharacterData
from ..data.occupation import OccupationData
from ..utils import (
    get_exact_or_unique_prefix_match,
    get_first_set_match,
    get_first_set_match_or_over_under_flow,
    get_unique_prefix_match,
)
from .state import (
    AbilityState,
    AugurState,
    CharacterState,
    ClassState,
    CritState,
    OccupationState,
    State,
)


class LocalAbilityData(BaseModel):
    model_config = ConfigDict(frozen=True)
    name: str
    description: str


class LocalAbilityModifierData(BaseModel):
    model_config = ConfigDict(frozen=True)
    score: int
    mod: int
    spells: int
    max_spell_level: int


class LocalAbilitiesData(BaseModel):
    model_config = ConfigDict(frozen=True)
    abilities: List[LocalAbilityData]
    modifiers: List[LocalAbilityModifierData]


class LocalAbilityState(AbilityState):
    def __init__(self):  # type: ignore
        self._abilities_data = LocalAbilitiesData(abilities=[], modifiers=[])
        path: Path = (
            Path(__file__).parent.parent / "bot" / "commands" / "abilities.json"
        )
        if path.exists():
            with path.open() as file_desc:
                self._abilities_data = LocalAbilitiesData.model_validate_json(
                    file_desc.read()
                )
        else:
            logging.warning("Unable to find %s", path)

    def get_all(self) -> List[AbilityData]:
        return cast(List[AbilityData], self._abilities_data.abilities)

    def get_from_prefix(self, prefix) -> AbilityData:
        return cast(
            AbilityData,
            get_unique_prefix_match(
                prefix, self._abilities_data.abilities, lambda a: a.name
            ),
        )

    def get_mods(self) -> List[AbilityModifierData]:
        return cast(List[AbilityModifierData], self._abilities_data.modifiers)

    def get_mod_from_score(self, score: int) -> AbilityModifierData:
        return cast(
            AbilityModifierData,
            get_first_set_match_or_over_under_flow(
                score, self._abilities_data.modifiers, lambda mod: [mod.score]
            ),
        )


class LocalAugurData(BaseModel):
    model_config = ConfigDict(frozen=True)
    description: str
    roll: int


class LocalAugursData(BaseModel):
    augurs: List[LocalAugurData]


class LocalAugurState(AugurState):
    def __init__(self):
        augurs_data = LocalAugursData(augurs=[])
        path: Path = Path(__file__).parent.parent / "bot" / "commands" / "augurs.json"
        if path.exists():
            with path.open() as file_desc:
                augurs_data = LocalAugursData.model_validate_json(file_desc.read())
        else:
            logging.warning("Unable to find %s", path)

        self._augurs_dict: Dict[int, LocalAugurData] = {
            aug.roll: aug for aug in augurs_data.augurs
        }

    def get_all(self) -> List[AugurData]:
        return cast(List[AugurData], list(self._augurs_dict.values()))

    def get_from_roll(self, roll: int) -> AugurData:
        return cast(AugurData, self._augurs_dict[roll])


class LocalCharacterData(BaseModel):
    name: str
    user: str
    active: bool = True
    level: int = 0
    strength: Union[int, None] = None
    agility: Union[int, None] = None
    stamina: Union[int, None] = None
    personality: Union[int, None] = None
    intelligence: Union[int, None] = None
    luck: Union[int, None] = None
    initial_luck: Union[int, None] = None
    hit_points: Union[int, None] = None
    equipment: Union[List[str], None] = None
    occupation: Union[int, None] = None
    exp: Union[int, None] = None
    alignment: Union[str, None] = None
    initiative: Union[int, None] = None
    initiative_time: Union[int, None] = None
    initiative_modifier: Union[int, None] = None
    hit_die: Union[int, None] = None
    augur: Union[int, None] = None
    cls: Union[str, None] = None


class LocalCharactersData(BaseModel):
    characters: List[LocalCharacterData]


class LocalCharacterState(CharacterState):
    def __init__(self):  # type: ignore
        chars_data = LocalCharactersData(characters=[])
        self._path: Path = (
            Path(__file__).parent.parent / "bot" / "commands" / "characters.json"
        )
        if self._path.exists():
            with self._path.open() as file_desc:
                chars_data = LocalCharactersData.model_validate_json(file_desc.read())
        else:
            logging.warning("Unable to find %s", self._path)

        self._characters: List[LocalCharacterData] = chars_data.characters

    def _get(self, name: str) -> CharacterData:
        candidates = [char for char in self.get_all() if char.name == name]
        if len(candidates) == 1:
            return candidates[0]
        raise KeyError(f"There are {len(candidates)} characters called {name}")

    def get_all(self) -> List[CharacterData]:
        return cast(List[CharacterData], self._characters)

    def get_from_tokens(
        self, tokens: Iterable[str], user: str, create: bool = False
    ) -> CharacterData:
        name: str = " ".join(tokens)
        return self.get_from_str(name, user, create)

    def get_from_str(self, name: str, user: str, create: bool = False) -> CharacterData:
        if name:
            return self.get_from_name(name, create, user)
        return self.get_from_user(user)

    def get_from_name(
        self, name: str, create: bool = False, user: Union[str, None] = None
    ) -> CharacterData:
        try:
            return cast(
                CharacterData,
                get_exact_or_unique_prefix_match(
                    name, self._characters, lambda cdi: cdi.name
                ),
            )
        except KeyError as err:
            if create and user:
                cdi: LocalCharacterData = LocalCharacterData(name=name, user=user)  # type: ignore
                self._characters.append(cdi)
                return cast(CharacterData, cdi)
            raise KeyError(f"Unable to find character with name '{name}'") from err

    def get_from_user(self, user: str) -> CharacterData:
        return cast(
            CharacterData,
            get_unique_prefix_match(
                user,
                tuple(filter(lambda char_data: char_data.active, self._characters)),
                lambda cdi: cdi.user,
            ),
        )

    def add_store_and_get(self, char_data: CharacterData) -> CharacterData:
        if any(char for char in self.get_all() if char.name == char_data.name):
            raise KeyError(f"Character with name '{char_data.name}' already exists")
        local_char_data = LocalCharacterData(**asdict(char_data))
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
        self._store()

    def _store(self) -> None:
        with open(self._path, "w", encoding="UTF8") as file_desc:
            file_desc.write(
                LocalCharactersData(characters=self._characters).model_dump_json()
            )


class LocalOccupationData(BaseModel):
    rolls: List[int]
    name: str
    weapon: str
    goods: str


class LocalOccupationsData(BaseModel):
    occupations: List[LocalOccupationData]


class LocalOccupationState(OccupationState):
    def __init__(self):  # type: ignore
        occupations_data: LocalOccupationsData = LocalOccupationsData(occupations=[])
        path: Path = (
            Path(__file__).parent.parent / "bot" / "commands" / "occupations.json"
        )
        if path.exists():
            with path.open() as file_desc:
                occupations_data = LocalOccupationsData.model_validate_json(
                    file_desc.read()
                )
        else:
            logging.warning("Unable to find %s", path)
        self._occupations: List[LocalOccupationData] = occupations_data.occupations

    def get_all(self) -> List[OccupationData]:
        return cast(List[OccupationData], self._occupations)

    def get_from_roll(self, roll: int) -> OccupationData:
        return get_first_set_match(roll, self.get_all(), lambda o: o.rolls)


class LocalSpellsByLevelData(BaseModel):
    model_config = ConfigDict(frozen=True)
    level: int
    spells: int


# pylint: disable=R0801
class LocalLevelData(BaseModel):
    level: int
    attack_die: str
    crit_die: str
    crit_table: int
    action_dice: List[str]
    ref: int
    fort: int
    will: int
    spells_by_level: List[LocalSpellsByLevelData]
    thief_luck_die: int
    threat_range: List[int]
    spells: int
    max_spell_level: int
    sneak_hide: int


class LocalClassData(BaseModel):
    name: str
    hit_die: int
    weapons: List[str]
    levels: List[LocalLevelData]


class LocalClassesData(BaseModel):
    classes: List[LocalClassData]


class LocalClassState(ClassState):
    def __init__(self):
        classes_data: LocalClassesData = LocalClassesData(classes=[])
        path: Path = Path(__file__).parent.parent / "bot" / "commands" / "classes.json"
        if path.exists():
            with path.open() as file_desc:
                classes_data = LocalClassesData.model_validate_json(file_desc.read())
        else:
            logging.warning("Unable to find %s", path)
        self._classes: Dict[str, LocalClassData] = {
            cls.name: cls for cls in classes_data.classes
        }

    def get_all(self) -> List[ClassData]:
        return cast(List[ClassData], list(self._classes.values()))

    def get_from_name(self, name: str) -> ClassData:
        return cast(ClassData, self._classes[name])


class LocalCritData(BaseModel):
    rolls: List[int]
    effect: str


class LocalCritTableData(BaseModel):
    number: int
    crits: List[LocalCritData]


class LocalCritTablesData(BaseModel):
    crit_tables: List[LocalCritTableData]


class LocalCritState(CritState):
    def __init__(self):
        data: LocalCritTablesData = LocalCritTablesData(crit_tables=[])
        path: Path = Path(__file__).parent.parent / "bot" / "commands" / "crits.json"
        if path.exists():
            with path.open() as file_desc:
                data = LocalCritTablesData.model_validate_json(file_desc.read())
        else:
            logging.warning("Unable to find %s", path)
        self._data: List[LocalCritTableData] = data.crit_tables

    def get_all(self) -> List[CritTableData]:
        return cast(List[CritTableData], self._data)

    def get_one(self, table: int) -> CritTableData:
        return cast(
            CritTableData, next(filter(lambda tbl: tbl.number == table, self._data))
        )


class LocalState(State):
    def __init__(self):  # type: ignore
        self._abilities = LocalAbilityState()
        self._augurs = LocalAugurState()
        self._characters = LocalCharacterState()
        self._occupations = LocalOccupationState()
        self._classes = LocalClassState()
        self._crits = LocalCritState()

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
