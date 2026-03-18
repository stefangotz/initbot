# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from collections.abc import Sequence
from dataclasses import dataclass

from initbot.base import BaseData


@dataclass(frozen=True)
class CritData(BaseData):
    rolls: Sequence[int]
    effect: str


@dataclass(frozen=True)
class CritTableData(BaseData):
    number: int
    crits: Sequence[CritData]
