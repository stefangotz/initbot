# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from collections.abc import Sequence
from typing import Protocol


# Implementations (LocalCritData/LocalCritTableData, _SqlCritData/_SqlCritTableData) satisfy
# these Protocols structurally. Explicit inheritance is not possible: _ProtocolMeta
# (typing.Protocol), Pydantic's ModelMetaclass, and Peewee's ModelBase are all ABCMeta
# subclasses but none is a subclass of another, so Python raises TypeError: metaclass
# conflict at class definition time. As a consequence, ty cannot verify that
# Sequence[LocalCritTableData] satisfies Sequence[CritTableData] without nominal subtyping,
# so LocalCritState.get_all() suppresses the resulting return-value error with a type: ignore.
class CritData(Protocol):
    rolls: Sequence[int]
    effect: str


class CritTableData(Protocol):
    number: int
    crits: Sequence[CritData]
