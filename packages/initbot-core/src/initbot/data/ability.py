from dataclasses import dataclass

from initbot.base import BaseData


@dataclass(frozen=True)
class AbilityData(BaseData):
    name: str
    description: str


@dataclass(frozen=True)
class AbilityModifierData(BaseData):
    score: int
    mod: int
    spells: int
    max_spell_level: int


@dataclass(frozen=True)
class AbilityScoreData(BaseData):
    abl: AbilityData
    score: int = 0
