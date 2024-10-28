from typing import List, Sequence, Union, Iterable

from ..data.ability import AbilityData, AbilityModifierData
from ..data.augur import AugurData
from ..data.character import CharacterData
from ..data.cls import ClassData
from ..data.crit import CritTableData
from ..data.occupation import OccupationData
from ..utils import (
    get_first_set_match,
    get_first_set_match_or_over_under_flow,
    get_unique_prefix_match,
)


class AbilityState:
    def get_all(self) -> Sequence[AbilityData]:
        raise NotImplementedError()

    def get_from_prefix(self, prefix: str) -> AbilityData:
        return get_unique_prefix_match(prefix, self.get_all(), lambda a: a.name)

    def get_mods(self) -> Sequence[AbilityModifierData]:
        raise NotImplementedError()

    def get_mod_from_score(self, score: int) -> AbilityModifierData:
        return get_first_set_match_or_over_under_flow(
            score, self.get_mods(), lambda mod: [mod.score]
        )


class AugurState:
    def get_all(self) -> Sequence[AugurData]:
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

    def add_store_and_get(self, char_data: CharacterData) -> CharacterData:
        raise NotImplementedError()

    def remove_and_store(self, char_data: CharacterData) -> None:
        raise NotImplementedError()

    def update_and_store(self, char_data: CharacterData) -> None:
        raise NotImplementedError()


class OccupationState:
    def get_all(self) -> Sequence[OccupationData]:
        raise NotImplementedError()

    def get_from_roll(self, roll: int) -> OccupationData:
        return get_first_set_match(roll, self.get_all(), lambda o: o.rolls)


class ClassState:
    def get_all(self) -> Sequence[ClassData]:
        raise NotImplementedError()

    def get_from_name(self, name: str) -> ClassData:
        return next(filter(lambda cd: cd.name == name, self.get_all()))


class CritState:
    def get_all(self) -> Sequence[CritTableData]:
        raise NotImplementedError()

    def get_one(self, table: int) -> CritTableData:
        return next(filter(lambda tbl: tbl.number == table, self.get_all()))


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
