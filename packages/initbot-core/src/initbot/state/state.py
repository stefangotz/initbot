from abc import ABC, abstractmethod
from collections.abc import Iterable, Sequence, Set
from typing import Union

import sys

# pylint: disable=no-name-in-module,wrong-import-position
if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

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


class PartialState(ABC):
    @abstractmethod
    def import_from(self, src: Self) -> None:
        raise NotImplementedError()


class AbilityState(PartialState, ABC):
    @abstractmethod
    def get_all(self) -> Sequence[AbilityData]:
        raise NotImplementedError()

    def get_from_prefix(self, prefix: str) -> AbilityData:
        return get_unique_prefix_match(prefix, self.get_all(), lambda a: a.name)

    @abstractmethod
    def get_mods(self) -> Sequence[AbilityModifierData]:
        raise NotImplementedError()

    def get_mod_from_score(self, score: int) -> AbilityModifierData:
        return get_first_set_match_or_over_under_flow(
            score, self.get_mods(), lambda mod: [mod.score]
        )

    @abstractmethod
    def import_from(self, src: "AbilityState") -> None:
        raise NotImplementedError()


class AugurState(PartialState, ABC):
    @abstractmethod
    def get_all(self) -> Sequence[AugurData]:
        raise NotImplementedError()

    def get_from_roll(self, roll: int) -> AugurData:
        return next(filter(lambda i: i.roll == roll, self.get_all()))

    @abstractmethod
    def import_from(self, src: "AugurState") -> None:
        raise NotImplementedError()


class CharacterState(PartialState, ABC):
    @abstractmethod
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

    @abstractmethod
    def add_store_and_get(self, char_data: CharacterData) -> CharacterData:
        raise NotImplementedError()

    @abstractmethod
    def remove_and_store(self, char_data: CharacterData) -> None:
        raise NotImplementedError()

    @abstractmethod
    def update_and_store(self, char_data: CharacterData) -> None:
        raise NotImplementedError()

    @abstractmethod
    def import_from(self, src: "CharacterState") -> None:
        raise NotImplementedError()


class OccupationState(PartialState, ABC):
    @abstractmethod
    def get_all(self) -> Sequence[OccupationData]:
        raise NotImplementedError()

    def get_from_roll(self, roll: int) -> OccupationData:
        return get_first_set_match(roll, self.get_all(), lambda o: o.rolls)

    @abstractmethod
    def import_from(self, src: "OccupationState") -> None:
        raise NotImplementedError()


class ClassState(PartialState, ABC):
    @abstractmethod
    def get_all(self) -> Sequence[ClassData]:
        raise NotImplementedError()

    def get_from_name(self, name: str) -> ClassData:
        return next(filter(lambda cd: cd.name == name, self.get_all()))

    @abstractmethod
    def import_from(self, src: "ClassState") -> None:
        raise NotImplementedError()


class CritState(PartialState, ABC):
    @abstractmethod
    def get_all(self) -> Sequence[CritTableData]:
        raise NotImplementedError()

    def get_one(self, table: int) -> CritTableData:
        return next(filter(lambda tbl: tbl.number == table, self.get_all()))

    @abstractmethod
    def import_from(self, src: "CritState") -> None:
        raise NotImplementedError()


class State(ABC):
    @property
    @abstractmethod
    def abilities(self) -> AbilityState:
        raise NotImplementedError()

    @property
    @abstractmethod
    def augurs(self) -> AugurState:
        raise NotImplementedError()

    @property
    @abstractmethod
    def characters(self) -> CharacterState:
        raise NotImplementedError()

    @property
    @abstractmethod
    def occupations(self) -> OccupationState:
        raise NotImplementedError()

    @property
    @abstractmethod
    def classes(self) -> ClassState:
        raise NotImplementedError()

    @property
    @abstractmethod
    def crits(self) -> CritState:
        raise NotImplementedError()

    def import_from(self, src: "State") -> None:
        target_attributes = {
            name: getattr(self, name) for name in dir(self) if not name.startswith("_")
        }
        target_states = {
            name: value
            for name, value in target_attributes.items()
            if issubclass(type(value), PartialState)
        }
        for target_state_name, target_state in target_states.items():
            print(f"Importing {target_state_name} from {src}")
            target_state.import_from(getattr(src, target_state_name))

    @classmethod
    @abstractmethod
    def get_supported_state_types(cls) -> Set[str]:
        """Return the types of state that this state class supports.

        The returned values are matched against the first part of the "state" setting (see config.py).
        For example, this function may return {"foo", "bar"} to declare that it can handle any state setting starting with "foo:" or "bar:".
        If Settings.state is "foo:sqlite:/bot.db", the factory will attempt to create an instance of the given State subclass by passing "foo:sqlite:/bot.db" to its constructor.
        """
        raise NotImplementedError()
