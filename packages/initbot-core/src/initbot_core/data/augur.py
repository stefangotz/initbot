# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from typing import Protocol


# Implementations (LocalAugurData, _SqlAugurData) satisfy this Protocol structurally.
# Explicit inheritance is not possible: _ProtocolMeta (typing.Protocol), Pydantic's
# ModelMetaclass, and Peewee's ModelBase are all ABCMeta subclasses but none is a subclass
# of another, so Python raises TypeError: metaclass conflict at class definition time.
class AugurData(Protocol):
    description: str
    roll: int
