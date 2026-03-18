from collections.abc import Sequence
from dataclasses import dataclass

from initbot.base import BaseData


@dataclass(frozen=True)
class CritData(BaseData):
    rolls: Sequence[int]
    effect: str


@dataclass(frozen=True)
class CritTableData(BaseData):
    number: int
    crits: Sequence[CritData]
