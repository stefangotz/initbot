from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class SpellsByLevelData:
    level: int
    spells: int


@dataclass(frozen=True)
class LevelData:
    level: int
    attack_die: str
    crit_die: str
    crit_table: int
    action_dice: Tuple[str, ...]
    ref: int
    fort: int
    will: int
    spells_by_level: Tuple[SpellsByLevelData, ...]
    thief_luck_die: int
    threat_range: Tuple[int, ...]
    spells: int
    max_spell_level: int
    sneak_hide: int


@dataclass(frozen=True)
class ClassData:
    name: str
    hit_die: int
    weapons: Tuple[str, ...]
    levels: Tuple[LevelData, ...]
