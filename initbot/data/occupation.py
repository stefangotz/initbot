from dataclasses import dataclass

from ..base import BaseData


@dataclass(frozen=True)
class OccupationData(BaseData):
    rolls: tuple[int, ...]
    name: str
    weapon: str
    goods: str
