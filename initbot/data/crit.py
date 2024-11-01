from dataclasses import dataclass
from typing import Tuple

from ..base import BaseData


@dataclass(frozen=True)
class CritData(BaseData):
    rolls: Tuple[int, ...]
    effect: str


@dataclass(frozen=True)
class CritTableData(BaseData):
    number: int
    crits: Tuple[CritData, ...]
