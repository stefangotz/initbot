from dataclasses import dataclass

from ..base import BaseData


@dataclass(frozen=True)
class AugurData(BaseData):
    description: str
    roll: int
