# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from collections.abc import Sequence
from typing import Protocol


# Implementations (LocalOccupationData, _SqlOccupationData) satisfy this Protocol
# structurally. Explicit inheritance is not possible: _ProtocolMeta (typing.Protocol),
# Pydantic's ModelMetaclass, and Peewee's ModelBase are all ABCMeta subclasses but none is
# a subclass of another, so Python raises TypeError: metaclass conflict at class definition.
# As a consequence, ty cannot verify that Sequence[LocalOccupationData] satisfies
# Sequence[OccupationData] without nominal subtyping, so LocalOccupationState.get_all()
# suppresses the resulting return-value error with a type: ignore comment.
class OccupationData(Protocol):
    rolls: Sequence[int]
    name: str
    weapon: str
    goods: str
