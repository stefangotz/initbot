# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from dataclasses import dataclass
from typing import Protocol


# Implementations (LocalAbilityData, _SqlAbilityData, etc.) satisfy these Protocols
# structurally. Explicit inheritance is not possible: _ProtocolMeta (typing.Protocol),
# Pydantic's ModelMetaclass, and Peewee's ModelBase are all ABCMeta subclasses but none is
# a subclass of another, so Python raises TypeError: metaclass conflict at class definition.
class AbilityData(Protocol):
    name: str
    description: str


class AbilityModifierData(Protocol):
    score: int
    mod: int
    spells: int
    max_spell_level: int


@dataclass(frozen=True)
class AbilityScoreData:
    abl: AbilityData
    score: int = 0
