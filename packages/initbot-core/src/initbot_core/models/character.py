# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import random
from collections.abc import Sequence

from initbot_core.data.ability import AbilityScoreData
from initbot_core.data.augur import AugurData
from initbot_core.data.character import CharacterData
from initbot_core.data.cls import ClassData
from initbot_core.data.occupation import OccupationData
from initbot_core.models.roll import NerdDiceRoll
from initbot_core.state.state import State
from initbot_core.utils import get_unique_prefix_match


class Character:  # pylint: disable=too-many-public-methods
    def __init__(self, cdi: CharacterData, state: State):
        self.cdi = cdi
        self._state = state

    @property
    def name(self) -> str:
        return self.cdi.name

    @name.setter
    def name(self, name: str) -> None:
        self.cdi.name = name

    @property
    def level(self) -> int:
        return self.cdi.level

    @level.setter
    def level(self, level: int) -> None:
        self.cdi.level = level

    @property
    def user(self) -> str:
        return self.cdi.user

    @user.setter
    def user(self, user: str) -> None:
        self.cdi.user = user

    @property
    def ability_scores(self) -> Sequence[AbilityScoreData]:
        return tuple(
            AbilityScoreData(abl=abl, score=getattr(self.cdi, abl.name.lower()))
            for abl in self._state.abilities.get_all()
            if getattr(self.cdi, abl.name.lower(), None)
        )

    def _get_ability_score(self, prefix: str) -> AbilityScoreData:
        return get_unique_prefix_match(
            prefix, self.ability_scores, lambda ability_score: ability_score.abl.name
        )

    @property
    def strength(self) -> AbilityScoreData | None:
        try:
            # TO DO: birth augur
            return self._get_ability_score("strength")
        except KeyError:
            pass
        return None

    @property
    def agility(self) -> AbilityScoreData | None:
        try:
            # TO DO: birth augur
            return self._get_ability_score("agility")
        except KeyError:
            pass
        return None

    @property
    def stamina(self) -> AbilityScoreData | None:
        try:
            # TO DO: birth augur
            return self._get_ability_score("stamina")
        except KeyError:
            pass
        return None

    @property
    def personality(self) -> AbilityScoreData | None:
        try:
            # TO DO: birth augur
            return self._get_ability_score("personality")
        except KeyError:
            pass
        return None

    @property
    def intelligence(self) -> AbilityScoreData | None:
        try:
            # TO DO: birth augur
            return self._get_ability_score("intelligence")
        except KeyError:
            pass
        return None

    @property
    def luck(self) -> AbilityScoreData | None:
        try:
            return self._get_ability_score("luck")
        except KeyError:
            pass
        return None

    @property
    def hit_points(self) -> int | None:
        return self.cdi.hit_points

    @hit_points.setter
    def hit_points(self, hit_points: int) -> None:
        self.cdi.hit_points = hit_points

    @property
    def initiative(self) -> int | None:
        return self.cdi.initiative

    @property
    def initiative_time(self) -> int | None:
        return self.cdi.initiative_time

    @property
    def initiative_modifier(self) -> int | None:
        mod = None
        if self.cdi.initiative_modifier is None:
            # TO DO: roll is modified by two-handed weapon (d16)
            if self.agility is not None:
                mod = self._state.abilities.get_mod_from_score(self.agility.score).mod
            if self.cdi.augur == 24:
                if self.cdi.initial_luck is not None:
                    if mod is None:
                        mod = 0
                    mod += self._state.abilities.get_mod_from_score(
                        self.cdi.initial_luck
                    ).mod
            if self.cls and self.cls.name == "warrior":
                if mod is None:
                    mod = 0
                mod += self.level
        else:
            mod = self.cdi.initiative_modifier
        return mod

    @initiative_modifier.setter
    def initiative_modifier(self, ini_mod: int) -> None:
        self.cdi.initiative_modifier = ini_mod

    @property
    def hit_die(self) -> NerdDiceRoll | None:
        if self.cdi.hit_die is not None:
            return NerdDiceRoll(self.cdi.hit_die)
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
    def augur(self) -> AugurData | None:
        if self.cdi.augur is not None:
            return self._state.augurs.get_from_roll(self.cdi.augur)
        return None

    @property
    def occupation(self) -> OccupationData | None:
        if self.cdi.occupation is not None:
            return self._state.occupations.get_from_roll(self.cdi.occupation)
        return None

    @property
    def cls(self) -> ClassData | None:
        if self.cdi.cls is not None:
            return self._state.classes.get_from_name(self.cdi.cls)
        return None

    @property
    def active(self) -> bool:
        return self.cdi.active

    @active.setter
    def active(self, new: bool) -> None:
        self.cdi.active = new

    @property
    def creation_time(self) -> int | None:
        return self.cdi.creation_time
