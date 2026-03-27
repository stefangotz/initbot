# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import time
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


# pylint: disable=R0801
@dataclass
class NewCharacterData:
    """Creation input — passed into add_store_and_get."""

    name: str
    user: str
    active: bool = True
    level: int = 0
    strength: int | None = None
    agility: int | None = None
    stamina: int | None = None
    personality: int | None = None
    intelligence: int | None = None
    luck: int | None = None
    initial_luck: int | None = None
    hit_points: int | None = None
    equipment: Sequence[str] | None = None
    occupation: int | None = None
    exp: int | None = None
    alignment: str | None = None
    initiative: int | None = None
    initiative_time: int | None = None
    initiative_modifier: int | None = None
    hit_die: int | None = None
    augur: int | None = None
    cls: str | None = None
    last_used: int | None = None
    player_id: int | None = None


# Implementations (LocalCharacterData, _SqlCharacterData) satisfy this Protocol structurally.
# Explicit inheritance is not possible: _ProtocolMeta (typing.Protocol), Pydantic's
# ModelMetaclass, and Peewee's ModelBase are all ABCMeta subclasses but none is a subclass
# of another, so Python raises TypeError: metaclass conflict at class definition time.
@runtime_checkable
class CharacterData(Protocol):
    """Data handle — the storage-native object returned by get_all() and mutated in place."""

    name: str
    user: str
    active: bool
    level: int
    strength: int | None
    agility: int | None
    stamina: int | None
    personality: int | None
    intelligence: int | None
    luck: int | None
    initial_luck: int | None
    hit_points: int | None
    equipment: Sequence[str] | None
    occupation: int | None
    exp: int | None
    alignment: str | None
    initiative: int | None
    initiative_time: int | None
    initiative_modifier: int | None
    hit_die: int | None
    augur: int | None
    cls: str | None
    last_used: int | None
    player_id: int | None


def is_eligible_for_pruning(cdi: CharacterData, threshold_days: int) -> bool:
    """Returns True if the character has not been used recently enough."""
    if cdi.last_used is None:
        return True
    return cdi.last_used < int(time.time()) - threshold_days * 86400
