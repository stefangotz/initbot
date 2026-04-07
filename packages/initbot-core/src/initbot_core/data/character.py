# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import time
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class NewCharacterData:
    """Creation input — passed into add_store_and_get."""

    name: str
    user: str
    player_id: int
    initiative: int | None = None
    initiative_dice: str | None = None
    last_used: int | None = None


@runtime_checkable
class CharacterData(Protocol):
    """Data handle — the storage-native object returned by get_all() and mutated in place."""

    name: str
    user: str
    initiative: int | None
    initiative_dice: str | None
    last_used: int | None
    player_id: int


def is_eligible_for_pruning(cdi: CharacterData, threshold_days: int) -> bool:
    """Returns True if the character has not been used recently enough."""
    if cdi.last_used is None:
        return True
    return cdi.last_used < int(time.time()) - threshold_days * 86400
