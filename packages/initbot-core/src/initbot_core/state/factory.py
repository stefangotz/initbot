# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from initbot_core.state.sql import SqlState
from initbot_core.state.state import State


def create_state_from_source(source: str) -> State:
    name = source.split(":", maxsplit=1)[0]
    if name == "sqlite":
        return SqlState(source)
    raise ValueError(f"Unknown kind of data store: {name}; supported: sqlite")
