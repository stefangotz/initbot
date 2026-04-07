# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from typing import Protocol, runtime_checkable


# Implementations (LocalPlayerData, _SqlPlayerData) satisfy this Protocol structurally.
# Explicit inheritance is not possible: _ProtocolMeta (typing.Protocol), Pydantic's
# ModelMetaclass, and Peewee's ModelBase are all ABCMeta subclasses but none is a subclass
# of another, so Python raises TypeError: metaclass conflict at class definition time.
@runtime_checkable
class PlayerData(Protocol):
    id: int  # Internal primary key, auto-assigned, used as foreign key by other entities
    discord_id: int  # Discord snowflake
    name: str  # Display name, refreshed on each command invocation
