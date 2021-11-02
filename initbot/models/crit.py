from typing import List
from pydantic import BaseModel


class CritModel(BaseModel):
    rolls: List[int]
    effect: str


class CritTable(BaseModel):
    number: int
    crits: List[CritModel]
