# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from collections.abc import Sequence
from typing import Protocol


# Implementations (LocalSpellsByLevelData/LocalLevelData/LocalClassData, and their _Sql*
# counterparts) satisfy these Protocols structurally. Explicit inheritance is not possible:
# _ProtocolMeta (typing.Protocol), Pydantic's ModelMetaclass, and Peewee's ModelBase are all
# ABCMeta subclasses but none is a subclass of another, so Python raises TypeError: metaclass
# conflict at class definition time. As a consequence, ty cannot verify that
# Sequence[LocalClassData] satisfies Sequence[ClassData] without nominal subtyping, so
# LocalClassState.get_all() suppresses the resulting return-value error with a type: ignore.
class SpellsByLevelData(Protocol):
    level: int
    spells: int


# pylint: disable=R0801
class LevelData(Protocol):
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


class ClassData(Protocol):
    name: str
    hit_die: int
    weapons: Sequence[str]
    levels: Sequence[LevelData]
