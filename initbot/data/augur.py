from typing import List

from pydantic import BaseModel


class AugurData(BaseModel):
    description: str
    roll: int


class AugursData(BaseModel):
    augurs: List[AugurData]
