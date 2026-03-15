from collections.abc import Sequence
from dataclasses import dataclass

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
    action_dice: Sequence[str]
    ref: int
    fort: int
    will: int
    spells_by_level: Sequence[SpellsByLevelData]
    thief_luck_die: int
    threat_range: Sequence[int]
    spells: int
    max_spell_level: int
    sneak_hide: int


@dataclass(frozen=True)
class ClassData(BaseData):
    name: str
    hit_die: int
    weapons: Sequence[str]
    levels: Sequence[LevelData]
