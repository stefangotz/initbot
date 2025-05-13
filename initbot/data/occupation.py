from collections.abc import Sequence
from dataclasses import dataclass

from ..base import BaseData


@dataclass(frozen=True)
class OccupationData(BaseData):
    rolls: Sequence[int]
    name: str
    weapon: str
    goods: str
