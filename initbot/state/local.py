from dataclasses import asdict
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple, Union, cast

from pydantic import BaseModel, ConfigDict

from initbot.data.cls import ClassData
from initbot.data.crit import CritTableData

from ..data.ability import AbilityData, AbilityModifierData
from ..data.augur import AugurData
from ..data.character import CharacterData
from ..data.occupation import OccupationData
from ..utils import (
    get_exact_or_unique_prefix_match,
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


class LocalBaseModel(BaseModel):
    def as_dict(self) -> Dict[str, Any]:
        return self.dict()


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
    abilities: Tuple[LocalAbilityData, ...] = ()
    modifiers: Tuple[LocalAbilityModifierData, ...] = ()


class LocalAbilityState(AbilityState):
    def __init__(self):  # type: ignore
        self._abilities_data = LocalAbilitiesData()
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

    def get_all(self) -> Sequence[AbilityData]:
        return cast(Tuple[AbilityData, ...], self._abilities_data.abilities)

    def get_mods(self) -> Sequence[AbilityModifierData]:
        return cast(Tuple[AbilityModifierData, ...], self._abilities_data.modifiers)


class LocalAugurData(LocalBaseModel):
    model_config = ConfigDict(frozen=True)
    description: str
    roll: int


class LocalAugursData(LocalBaseModel):
    model_config = ConfigDict(frozen=True)
    augurs: Tuple[LocalAugurData, ...] = ()


class LocalAugurState(AugurState):
    def __init__(self):
        augurs_data = LocalAugursData()
        path: Path = Path(__file__).parent.parent / "bot" / "commands" / "augurs.json"
        if path.exists():
            with path.open() as file_desc:
                augurs_data = LocalAugursData.model_validate_json(file_desc.read())
        else:
            logging.warning("Unable to find %s", path)

        self._augurs_dict: Dict[int, LocalAugurData] = {
            aug.roll: aug for aug in augurs_data.augurs
        }

    def get_all(self) -> Sequence[AugurData]:
        return cast(Tuple[AugurData, ...], tuple(self._augurs_dict.values()))

    def get_from_roll(self, roll: int) -> AugurData:
        return cast(AugurData, self._augurs_dict[roll])


class LocalCharacterData(LocalBaseModel):
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


class LocalCharactersData(LocalBaseModel):
    characters: List[LocalCharacterData] = []


class LocalCharacterState(CharacterState):
    def __init__(self):  # type: ignore
        chars_data = LocalCharactersData()
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


class LocalOccupationData(LocalBaseModel):
    model_config = ConfigDict(frozen=True)
    rolls: Tuple[int, ...]
    name: str
    weapon: str
    goods: str


class LocalOccupationsData(LocalBaseModel):
    model_config = ConfigDict(frozen=True)
    occupations: Tuple[LocalOccupationData, ...] = ()


class LocalOccupationState(OccupationState):
    def __init__(self):  # type: ignore
        occupations_data: LocalOccupationsData = LocalOccupationsData()
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
        self._occupations: Tuple[LocalOccupationData, ...] = (
            occupations_data.occupations
        )

    def get_all(self) -> Sequence[OccupationData]:
        return cast(Tuple[OccupationData, ...], self._occupations)


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
    action_dice: Tuple[str, ...]
    ref: int
    fort: int
    will: int
    spells_by_level: Tuple[LocalSpellsByLevelData, ...]
    thief_luck_die: int
    threat_range: Tuple[int, ...]
    spells: int
    max_spell_level: int
    sneak_hide: int


class LocalClassData(LocalBaseModel):
    model_config = ConfigDict(frozen=True)
    name: str
    hit_die: int
    weapons: Tuple[str, ...]
    levels: Tuple[LocalLevelData, ...]


class LocalClassesData(LocalBaseModel):
    model_config = ConfigDict(frozen=True)
    classes: Tuple[LocalClassData, ...] = ()


class LocalClassState(ClassState):
    def __init__(self):
        classes_data: LocalClassesData = LocalClassesData()
        path: Path = Path(__file__).parent.parent / "bot" / "commands" / "classes.json"
        if path.exists():
            with path.open() as file_desc:
                classes_data = LocalClassesData.model_validate_json(file_desc.read())
        else:
            logging.warning("Unable to find %s", path)
        self._classes: Tuple[LocalClassData, ...] = classes_data.classes

    def get_all(self) -> Sequence[ClassData]:
        return cast(Tuple[ClassData, ...], tuple(self._classes))


class LocalCritData(LocalBaseModel):
    model_config = ConfigDict(frozen=True)
    rolls: Tuple[int, ...]
    effect: str


class LocalCritTableData(LocalBaseModel):
    model_config = ConfigDict(frozen=True)
    number: int
    crits: Tuple[LocalCritData, ...]


class LocalCritTablesData(LocalBaseModel):
    model_config = ConfigDict(frozen=True)
    crit_tables: Tuple[LocalCritTableData, ...] = ()


class LocalCritState(CritState):
    def __init__(self):
        data: LocalCritTablesData = LocalCritTablesData()
        path: Path = Path(__file__).parent.parent / "bot" / "commands" / "crits.json"
        if path.exists():
            with path.open() as file_desc:
                data = LocalCritTablesData.model_validate_json(file_desc.read())
        else:
            logging.warning("Unable to find %s", path)
        self._data: Tuple[LocalCritTableData, ...] = data.crit_tables

    def get_all(self) -> Sequence[CritTableData]:
        return cast(Tuple[CritTableData, ...], self._data)


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
