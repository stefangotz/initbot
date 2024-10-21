from typing import List, Union, Iterable

from initbot.data.cls import ClassData

from ..data.ability import AbilityData, AbilityModifierData
from ..data.augur import AugurData
from ..data.character import CharacterData
from ..data.crit import CritTableData
from ..data.occupation import OccupationData


class AbilityState:
    def get_all(self) -> List[AbilityData]:
        raise NotImplementedError()

    def get_from_prefix(self, prefix: str) -> AbilityData:
        raise NotImplementedError()

    def get_mods(self) -> List[AbilityModifierData]:
        raise NotImplementedError()

    def get_mod_from_score(self, score: int) -> AbilityModifierData:
        raise NotImplementedError()


class AugurState:
    def get_all(self) -> List[AugurData]:
        raise NotImplementedError()

    def get_from_roll(self, roll: int) -> AugurData:
        raise NotImplementedError()


class CharacterState:
    def get_all(self) -> List[CharacterData]:
        raise NotImplementedError()

    def get_from_tokens(
        self, tokens: Iterable[str], user: str, create: bool = False
    ) -> CharacterData:
        raise NotImplementedError()

    def get_from_str(self, name: str, user: str, create: bool = False) -> CharacterData:
        raise NotImplementedError()

    def get_from_name(
        self, name: str, create: bool = False, user: Union[str, None] = None
    ) -> CharacterData:
        raise NotImplementedError()

    def get_from_user(self, user: str) -> CharacterData:
        raise NotImplementedError()

    def add_and_store(self, char_data: CharacterData):
        raise NotImplementedError()

    def remove_and_store(self, char_data: CharacterData):
        raise NotImplementedError()

    def update_and_store(self, char_data: CharacterData):
        raise NotImplementedError()


class OccupationState:
    def get_all(self) -> List[OccupationData]:
        raise NotImplementedError()

    def get_from_roll(self, roll: int) -> OccupationData:
        raise NotImplementedError()


class ClassState:
    def get_all(self) -> List[ClassData]:
        raise NotImplementedError()

    def get_from_name(self, name: str) -> ClassData:
        raise NotImplementedError()


class CritState:
    def get_all(self) -> List[CritTableData]:
        raise NotImplementedError()

    def get_one(self, table: int) -> CritTableData:
        return self.get_all()[table]


class State:
    @property
    def abilities(self) -> AbilityState:
        raise NotImplementedError()

    @property
    def augurs(self) -> AugurState:
        raise NotImplementedError()

    @property
    def characters(self) -> CharacterState:
        raise NotImplementedError()

    @property
    def occupations(self) -> OccupationState:
        raise NotImplementedError()

    @property
    def classes(self) -> ClassState:
        raise NotImplementedError()

    @property
    def crits(self) -> CritState:
        raise NotImplementedError()
