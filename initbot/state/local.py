from pathlib import Path
from typing import Dict, List
import logging

from ..data.augur import AugurData, AugursData
from .state import State, AugurState


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


class LocalState(State):
    def __init__(self):
        self._augurs = LocalAugurState()

    @property
    def augurs(self) -> AugurState:
        return self._augurs
