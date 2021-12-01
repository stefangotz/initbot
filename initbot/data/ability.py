from typing import List

from pydantic import BaseModel


class AbilityData(BaseModel):
    name: str
    description: str


class AbilityModifierData(BaseModel):
    score: int
    mod: int
    spells: int
    max_spell_level: int


class AbilitiesData(BaseModel):
    abilities: List[AbilityData]
    modifiers: List[AbilityModifierData]


class AbilityScoreData(BaseModel):
    abl: AbilityData
    score: int = 0
