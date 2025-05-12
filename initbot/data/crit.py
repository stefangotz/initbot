from dataclasses import dataclass

from ..base import BaseData


@dataclass(frozen=True)
class CritData(BaseData):
    rolls: tuple[int, ...]
    effect: str


@dataclass(frozen=True)
class CritTableData(BaseData):
    number: int
    crits: tuple[CritData, ...]
