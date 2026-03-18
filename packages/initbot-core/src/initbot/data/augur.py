from dataclasses import dataclass

from initbot.base import BaseData


@dataclass(frozen=True)
class AugurData(BaseData):
    description: str
    roll: int
