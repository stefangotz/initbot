from typing import List


from ..data.augur import AugurData
from ..data.occupation import OccupationData


class AugurState:
    def get_all(self) -> List[AugurData]:
        raise NotImplementedError()

    def get_from_roll(self, roll: int) -> AugurData:
        raise NotImplementedError()


class OccupationState:
    def get_all(self) -> List[OccupationData]:
        raise NotImplementedError()

    def get_from_roll(self, roll: int) -> OccupationData:
        raise NotImplementedError()


class State:
    @property
    def augurs(self) -> AugurState:
        raise NotImplementedError()

    @property
    def occupations(self) -> OccupationState:
        raise NotImplementedError()
