from typing import FrozenSet, Any

from .init import init
from .roll import roll
from .character import cha, cha_new
from .equipment import equipment
from .occupation import occupations
from .abilities import abls, abl, asms, asm

commands: FrozenSet[Any] = frozenset(
    (init, roll, cha, equipment, occupations, abls, abl, asms, asm)
)
