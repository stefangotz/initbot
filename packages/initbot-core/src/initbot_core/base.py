# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from collections.abc import Mapping
from dataclasses import asdict
from typing import Any


class BaseData:
    def as_dict(self) -> Mapping[str, Any]:
        return asdict(self)  # type: ignore
