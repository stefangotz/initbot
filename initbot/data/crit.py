from typing import List
from pydantic import BaseModel


class CritData(BaseModel):
    rolls: List[int]
    effect: str


class CritTableData(BaseModel):
    number: int
    crits: List[CritData]


class CritTablesData(BaseModel):
    crit_tables: List[CritTableData]
