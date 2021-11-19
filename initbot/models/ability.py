from typing import List

from pydantic import BaseModel


class AbilityModel(BaseModel):
    name: str
    description: str


class AbilitiesModel(BaseModel):
    abilities: List[AbilityModel]


class AbilityScoreModifierModel(BaseModel):
    score: int
    mod: int
    spells: int
    max_spell_level: int


class AbilityScoreModel(BaseModel):
    abl: AbilityModel
    score: int = 0
