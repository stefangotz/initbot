from pathlib import Path
from typing import Dict, List
import logging

from ..data.ability import AbilitiesData, AbilityData, AbilityModifierData
from ..data.augur import AugurData, AugursData
from ..data.occupation import OccupationData, OccupationsData
from ..utils import get_first_set_match, get_unique_prefix_match, get_first_match
from .state import State, AbilityState, AugurState, OccupationState


class LocalAbilityState:
    def __init__(self):
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
        return get_first_match(score, self._abilities_data.modifiers, lambda m: m.score)


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


class LocalOccupationState:
    def __init__(self):
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


class LocalState(State):
    def __init__(self):
        self._abilities = LocalAbilityState()
        self._augurs = LocalAugurState()
        self._occupations = LocalOccupationState()

    @property
    def abilities(self) -> AbilityState:
        return self._abilities

    @property
    def augurs(self) -> AugurState:
        return self._augurs

    @property
    def occupations(self) -> OccupationState:
        return self._occupations
