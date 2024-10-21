from dataclasses import dataclass


@dataclass(frozen=True)
class AbilityData:
    name: str
    description: str


@dataclass(frozen=True)
class AbilityModifierData:
    score: int
    mod: int
    spells: int
    max_spell_level: int


@dataclass(frozen=True)
class AbilityScoreData:
    abl: AbilityData
    score: int = 0
