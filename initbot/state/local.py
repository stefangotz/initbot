from pathlib import Path
from typing import Dict, List
import logging

from ..data.augur import AugurData, AugursData
from ..data.occupation import OccupationData, OccupationsData
from ..utils import get_first_set_match
from .state import State, AugurState, OccupationState


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
        self._augurs = LocalAugurState()
        self._occupations = LocalOccupationState()

    @property
    def augurs(self) -> AugurState:
        return self._augurs

    @property
    def occupations(self) -> OccupationState:
        return self._occupations
