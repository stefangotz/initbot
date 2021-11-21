from pydantic import BaseModel


class AugurData(BaseModel):
    description: str
    roll: int
