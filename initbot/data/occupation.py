from dataclasses import dataclass
from typing import Tuple

from ..base import BaseData


@dataclass(frozen=True)
class OccupationData(BaseData):
    rolls: Tuple[int, ...]
    name: str
    weapon: str
    goods: str
