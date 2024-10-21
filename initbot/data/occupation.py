from dataclasses import dataclass
from typing import List


@dataclass
class OccupationData:
    rolls: List[int]
    name: str
    weapon: str
    goods: str
