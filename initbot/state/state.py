from typing import List

from ..data.augur import AugurData


class AugurState:
    def get_all(self) -> List[AugurData]:
        raise NotImplementedError()

    def get_from_roll(self, roll: int) -> AugurData:
        raise NotImplementedError()


class State:
    @property
    def augurs(self) -> AugurState:
        raise NotImplementedError()
