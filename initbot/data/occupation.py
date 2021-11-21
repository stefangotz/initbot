from typing import List
from pydantic import BaseModel


class OccupationData(BaseModel):
    rolls: List[int]
    name: str
    weapon: str
    goods: str


class OccupationsData(BaseModel):
    occupations: List[OccupationData]
