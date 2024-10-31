from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class CritData:
    rolls: Tuple[int, ...]
    effect: str


@dataclass(frozen=True)
class CritTableData:
    number: int
    crits: Tuple[CritData, ...]
