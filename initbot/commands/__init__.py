from typing import FrozenSet, Any

from .init import init
from .roll import roll
from .character import char_new, char_set
from .equipment import equipment
from .occupation import occupations
from .abilities import abls, abl, asms, asm

commands: FrozenSet[Any] = frozenset(
    (init, roll, char_new, char_set, equipment, occupations, abls, abl, asms, asm)
)
