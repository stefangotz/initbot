from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class SpellsByLevelData:
    level: int
    spells: int


@dataclass
class LevelData:
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


@dataclass
class ClassData:
    name: str
    hit_die: int
    weapons: List[str]
    levels: List[LevelData]
