# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from collections.abc import Sequence
from dataclasses import dataclass

from initbot_core.base import BaseData


# pylint: disable=R0801
@dataclass
class CharacterData(BaseData):
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
    creation_time: int | None = None
