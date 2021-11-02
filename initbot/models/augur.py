from pydantic import BaseModel


class AugurModel(BaseModel):
    description: str
    roll: int
