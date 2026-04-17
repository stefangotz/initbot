# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import time
from dataclasses import dataclass


@dataclass
class NewCharacterData:
    """Creation input — passed into add_store_and_get."""

    name: str
    player_id: int
    initiative: int | None = None
    initiative_dice: str | None = None
    last_used: int | None = None


@dataclass
class CharacterData:
    """Data handle returned by the storage layer and mutated in place before update_and_store."""

    name: str
    player_id: int
    initiative: int | None = None
    initiative_dice: str | None = None
    last_used: int | None = None


def is_eligible_for_pruning(cdi: CharacterData, threshold_days: int) -> bool:
    """Returns True if the character has not been used recently enough."""
    if cdi.last_used is None:
        return True
    return cdi.last_used < int(time.time()) - threshold_days * 86400
