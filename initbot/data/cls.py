from typing import List

from pydantic import BaseModel


class SpellsByLevelData(BaseModel):
    level: int
    spells: int


class LevelData(BaseModel):
    level: int
    attack_die: str
    crit_die: str
    crit_table: int
    action_dice: List[str]
    ref: int
    fort: int
    will: int
    spells_by_level: List[SpellsByLevelData]
    thief_luck_die: int
    threat_range: List[int]
    spells: int
    max_spell_level: int
    sneak_hide: int


class ClassData(BaseModel):
    name: str
    hit_die: int
    weapons: List[str]
    levels: List[LevelData]


class ClassesData(BaseModel):
    classes: List[ClassData]
