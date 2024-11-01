from dataclasses import dataclass
from typing import Tuple

from ..base import BaseData


@dataclass(frozen=True)
class SpellsByLevelData(BaseData):
    level: int
    spells: int


@dataclass(frozen=True)
class LevelData(BaseData):
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
class ClassData(BaseData):
    name: str
    hit_die: int
    weapons: Tuple[str, ...]
    levels: Tuple[LevelData, ...]
