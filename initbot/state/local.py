from pathlib import Path
from typing import Dict, List
import logging

from ..data.ability import AbilitiesData, AbilityData
from ..data.augur import AugurData, AugursData
from ..data.occupation import OccupationData, OccupationsData
from ..utils import get_first_set_match, get_unique_prefix_match
from .state import State, AbilityState, AugurState, OccupationState


class LocalAbilityState:
    def __init__(self):
        abilities_data = AbilitiesData(abilities=[])
        path: Path = (
            Path(__file__).parent.parent / "bot" / "commands" / "abilities.json"
        )
        if path.exists():
            abilities_data = AbilitiesData.parse_file(path)
        else:
            logging.warning("Unable to find %s", path)
        self._abilities = abilities_data.abilities

    def get_all(self) -> List[AbilityData]:
        return self._abilities

    def get_from_prefix(self, prefix) -> AbilityData:
        return get_unique_prefix_match(prefix, self._abilities, lambda a: a.name)


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
