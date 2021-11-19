from typing import List
from pydantic import BaseModel


class CritModel(BaseModel):
    rolls: List[int]
    effect: str


class CritTableModel(BaseModel):
    number: int
    crits: List[CritModel]


class CritTablesModel(BaseModel):
    crit_tables: List[CritTableModel]
