from typing import Sequence, Union, Iterable

from ..data.ability import AbilityData, AbilityModifierData
from ..data.augur import AugurData
from ..data.character import CharacterData
from ..data.cls import ClassData
from ..data.crit import CritTableData
from ..data.occupation import OccupationData
from ..utils import (
    get_exact_or_unique_prefix_match,
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
        return next(filter(lambda i: i.roll == roll, self.get_all()))


class CharacterState:
    def get_all(self) -> Sequence[CharacterData]:
        raise NotImplementedError()

    def get_from_tokens(
        self, tokens: Iterable[str], user: str, create: bool = False
    ) -> CharacterData:
        return self.get_from_str(" ".join(tokens), user, create)

    def get_from_str(self, name: str, user: str, create: bool = False) -> CharacterData:
        if name:
            return self.get_from_name(name, create, user)
        return self.get_from_user(user)

    def get_from_name(
        self, name: str, create: bool = False, user: Union[str, None] = None
    ) -> CharacterData:
        try:
            return get_exact_or_unique_prefix_match(
                name, self.get_all(), lambda cdi: cdi.name
            )
        except KeyError as err:
            if create and user:
                return self.add_store_and_get(CharacterData(name=name, user=user))
            raise KeyError(f"Unable to find character with name '{name}'") from err

    def get_from_user(self, user: str) -> CharacterData:
        return get_unique_prefix_match(
            user,
            tuple(filter(lambda char_data: char_data.active, self.get_all())),
            lambda cdi: cdi.user,
        )

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
