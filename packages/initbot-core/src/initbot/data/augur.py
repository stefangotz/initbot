# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from dataclasses import dataclass

from initbot.base import BaseData


@dataclass(frozen=True)
class AugurData(BaseData):
    description: str
    roll: int
