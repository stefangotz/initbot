from pydantic import BaseModel


class AbilityModel(BaseModel):
    name: str
    description: str


class AbilityScoreModifierModel(BaseModel):
    score: int
    mod: int
    spells: int
    max_spell_level: int


class AbilityScoreModel(BaseModel):
    abl: AbilityModel
    score: int = 0
