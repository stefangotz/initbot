from typing import List
from pydantic import BaseModel


class OccupationModel(BaseModel):
    rolls: List[int]
    name: str
    weapon: str
    goods: str


class OccupationsModel(BaseModel):
    occupations: List[OccupationModel]
