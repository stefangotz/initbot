from dataclasses import dataclass
from typing import List


@dataclass
class CritData:
    rolls: List[int]
    effect: str


@dataclass
class CritTableData:
    number: int
    crits: List[CritData]
