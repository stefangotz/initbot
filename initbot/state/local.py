import json
import logging
from pathlib import Path
from typing import Dict, Iterable, List, Union

from pydantic.json import pydantic_encoder

from initbot.data.cls import ClassData, ClassesData
from initbot.data.crit import CritTableData, CritTablesData

from ..data.ability import AbilitiesData, AbilityData, AbilityModifierData
from ..data.augur import AugurData, AugursData
from ..data.character import CharacterData, CharactersData
from ..data.occupation import OccupationData, OccupationsData
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


class LocalAbilityState(AbilityState):
    def __init__(self):  # type: ignore
        self._abilities_data = AbilitiesData(abilities=[], modifiers=[])
        path: Path = (
            Path(__file__).parent.parent / "bot" / "commands" / "abilities.json"
        )
        if path.exists():
            self._abilities_data = AbilitiesData.parse_file(path)
        else:
            logging.warning("Unable to find %s", path)

    def get_all(self) -> List[AbilityData]:
        return self._abilities_data.abilities

    def get_from_prefix(self, prefix) -> AbilityData:
        return get_unique_prefix_match(
            prefix, self._abilities_data.abilities, lambda a: a.name
        )

    def get_mods(self) -> List[AbilityModifierData]:
        return self._abilities_data.modifiers

    def get_mod_from_score(self, score: int) -> AbilityModifierData:
        return get_first_set_match_or_over_under_flow(
            score, self._abilities_data.modifiers, lambda mod: [mod.score]
        )


class LocalAugurState(AugurState):
    def __init__(self):
        augurs_data = AugursData(augurs=[])
        path: Path = Path(__file__).parent.parent / "bot" / "commands" / "augurs.json"
        if path.exists():
            augurs_data = AugursData.parse_file(path)
        else:
            logging.warning("Unable to find %s", path)

        self._augurs_dict: Dict[int, AugurData] = {
            aug.roll: aug for aug in augurs_data.augurs
        }

    def get_all(self) -> List[AugurData]:
        return list(self._augurs_dict.values())

    def get_from_roll(self, roll: int) -> AugurData:
        return self._augurs_dict[roll]


class LocalCharacterState(CharacterState):
    def __init__(self):  # type: ignore
        chars_data = CharactersData(characters=[])
        self._path: Path = (
            Path(__file__).parent.parent / "bot" / "commands" / "characters.json"
        )
        if self._path.exists():
            chars_data = CharactersData.parse_file(self._path)
        else:
            logging.warning("Unable to find %s", self._path)

        self._characters: List[CharacterData] = chars_data.characters

    def _get(self, name: str) -> CharacterData:
        candidates = [char for char in self.get_all() if char.name == name]
        if len(candidates) == 1:
            return candidates[0]
        raise KeyError(f"There are {len(candidates)} characters called {name}")

    def get_all(self) -> List[CharacterData]:
        return self._characters

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
            return get_exact_or_unique_prefix_match(
                name, self._characters, lambda cdi: cdi.name
            )
        except KeyError as err:
            if create and user:
                cdi: CharacterData = CharacterData(name=name, user=user)  # type: ignore
                self._characters.append(cdi)
                return cdi
            raise KeyError(f"Unable to find character with name '{name}'") from err

    def get_from_user(self, user: str) -> CharacterData:
        return get_unique_prefix_match(
            user,
            tuple(filter(lambda char_data: char_data.active, self._characters)),
            lambda cdi: cdi.user,
        )

    def add_and_store(self, char_data: CharacterData):
        if any(char for char in self.get_all() if char.name == char_data.name):
            raise KeyError(f"Character with name '{char_data.name}' already exists")
        self._characters.append(char_data)
        self._store()

    def remove_and_store(self, char_data: CharacterData):
        self._characters.remove(char_data)
        self._store()

    def update_and_store(self, char_data: CharacterData):
        existing_char = self._get(char_data.name)
        if id(existing_char) != id(char_data):
            self._characters = [
                char for char in self._characters if char.name != char_data.name
            ]
            self._characters.append(char_data)
        self._store()

    def _store(self):
        with open(self._path, "w", encoding="UTF8") as file_desc:
            json.dump(
                CharactersData(characters=self._characters),
                file_desc,
                default=pydantic_encoder,
            )


class LocalOccupationState(OccupationState):
    def __init__(self):  # type: ignore
        occupations_data: OccupationsData = OccupationsData(occupations=[])
        path: Path = (
            Path(__file__).parent.parent / "bot" / "commands" / "occupations.json"
        )
        if path.exists():
            occupations_data = OccupationsData.parse_file(path)
        else:
            logging.warning("Unable to find %s", path)
        self._occupations: List[OccupationData] = occupations_data.occupations

    def get_all(self) -> List[OccupationData]:
        return self._occupations

    def get_from_roll(self, roll: int) -> OccupationData:
        return get_first_set_match(roll, self.get_all(), lambda o: o.rolls)


class LocalClassState(ClassState):
    def __init__(self):
        classes_data: ClassesData = ClassesData(classes=[])
        path: Path = Path(__file__).parent.parent / "bot" / "commands" / "classes.json"
        if path.exists():
            classes_data = ClassesData.parse_file(path)
        else:
            logging.warning("Unable to find %s", path)
        self._classes: Dict[str, ClassData] = {
            cls.name: cls for cls in classes_data.classes
        }

    def get_all(self) -> List[ClassData]:
        return list(self._classes.values())

    def get_from_name(self, name: str) -> ClassData:
        return self._classes[name]


class LocalCritState(CritState):
    def __init__(self):
        data: CritTablesData = CritTablesData(crit_tables=[])
        path: Path = Path(__file__).parent.parent / "bot" / "commands" / "crits.json"
        if path.exists():
            with path.open() as file_desc:
                data = CritTablesData.model_validate_json(file_desc.read())
        else:
            logging.warning("Unable to find %s", path)
        self._data: List[CritTableData] = data.crit_tables

    def get_all(self) -> List[CritTableData]:
        return self._data

    def get_one(self, table: int) -> CritTableData:
        return next(filter(lambda tbl: tbl.number == table, self._data))


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
