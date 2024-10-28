from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class OccupationData:
    rolls: Tuple[int, ...]
    name: str
    weapon: str
    goods: str
