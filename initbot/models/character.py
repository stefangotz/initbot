from typing import List, Union
import random

from initbot.data.cls import ClassData

from ..data.ability import AbilityScoreData
from ..data.augur import AugurData
from ..data.character import CharacterData
from ..data.occupation import OccupationData
from ..state.state import State
from ..utils import get_unique_prefix_match
from .roll import DieRoll


class Character:
    def __init__(self, cdi: CharacterData, state: State):
        self.cdi = cdi
        self._state = state

    @property
    def name(self) -> str:
        return self.cdi.name

    @name.setter
    def name(self, name: str):
        self.cdi.name = name

    @property
    def user(self) -> str:
        return self.cdi.user

    @user.setter
    def user(self, user: str):
        self.cdi.user = user

    @property
    def ability_scores(self) -> List[AbilityScoreData]:
        return [
            AbilityScoreData(abl=abl, score=vars(self.cdi)[abl.name.lower()])
            for abl in self._state.abilities.get_all()
            if vars(self.cdi).get(abl.name.lower())
        ]

    def _get_ability_score(self, prefix: str) -> AbilityScoreData:
        return get_unique_prefix_match(
            prefix, self.ability_scores, lambda ability_score: ability_score.abl.name
        )

    @property
    def strength(self) -> Union[AbilityScoreData, None]:
        try:
            # TO DO: birth augur
            return self._get_ability_score("strength")
        except KeyError:
            pass
        return None

    @property
    def agility(self) -> Union[AbilityScoreData, None]:
        try:
            # TO DO: birth augur
            return self._get_ability_score("agility")
        except KeyError:
            pass
        return None

    @property
    def stamina(self) -> Union[AbilityScoreData, None]:
        try:
            # TO DO: birth augur
            return self._get_ability_score("stamina")
        except KeyError:
            pass
        return None

    @property
    def personality(self) -> Union[AbilityScoreData, None]:
        try:
            # TO DO: birth augur
            return self._get_ability_score("personality")
        except KeyError:
            pass
        return None

    @property
    def intelligence(self) -> Union[AbilityScoreData, None]:
        try:
            # TO DO: birth augur
            return self._get_ability_score("intelligence")
        except KeyError:
            pass
        return None

    @property
    def luck(self) -> Union[AbilityScoreData, None]:
        try:
            return self._get_ability_score("luck")
        except KeyError:
            pass
        return None

    @property
    def hit_points(self) -> Union[int, None]:
        return self.cdi.hit_points

    @hit_points.setter
    def hit_points(self, hit_points: int):
        self.cdi.hit_points = hit_points

    @property
    def initiative(self) -> Union[int, None]:
        return self.cdi.initiative

    @property
    def initiative_modifier(self) -> Union[int, None]:
        mod = None
        if self.cdi.initiative_modifier is None:
            # TO DO: modify by class (warrior gets +level)
            # roll is also modified by two-handed weapon (d16)
            if self.agility is not None:
                mod = self._state.abilities.get_mod_from_score(self.agility.score).mod
            if self.cdi.augur == 24:
                if self.cdi.initial_luck is not None:
                    if mod is None:
                        mod = 0
                    mod += self._state.abilities.get_mod_from_score(
                        self.cdi.initial_luck
                    ).mod
        else:
            mod = self.cdi.initiative_modifier
        return mod

    @initiative_modifier.setter
    def initiative_modifier(self, ini_mod: int):
        self.cdi.initiative_modifier = ini_mod

    @property
    def hit_die(self) -> Union[DieRoll, None]:
        if self.cdi.hit_die is not None:
            return DieRoll(self.cdi.hit_die)
        # TO DO: derive from class
        return None

    def initiative_comparison_value(self) -> int:
        if self.cdi.initiative is None:
            return -1

        ini = self.cdi.initiative * 1000000
        if self.agility is not None:
            ini += self.agility.score * 10000
        if self.hit_die is not None:
            ini += self.hit_die.sides * 100
        ini += random.randint(0, 99)

        return ini

    @property
    def augur(self) -> Union[AugurData, None]:
        if self.cdi.augur is not None:
            return self._state.augurs.get_from_roll(self.cdi.augur)
        return None

    @property
    def occupation(self) -> Union[OccupationData, None]:
        if self.cdi.occupation is not None:
            return self._state.occupations.get_from_roll(self.cdi.occupation)
        return None

    @property
    def cls(self) -> Union[ClassData, None]:
        if self.cdi.cls is not None:
            return self._state.classes.get_from_name(self.cdi.cls)
        return None
