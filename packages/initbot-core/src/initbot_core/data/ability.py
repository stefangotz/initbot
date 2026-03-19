# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from dataclasses import dataclass

from initbot_core.base import BaseData


@dataclass(frozen=True)
class AbilityData(BaseData):
    name: str
    description: str


@dataclass(frozen=True)
class AbilityModifierData(BaseData):
    score: int
    mod: int
    spells: int
    max_spell_level: int


@dataclass(frozen=True)
class AbilityScoreData(BaseData):
    abl: AbilityData
    score: int = 0
