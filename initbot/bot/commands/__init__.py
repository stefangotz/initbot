from typing import FrozenSet, Any

from .crit import crit
from .init import init, inis
from .roll import roll
from .character import new, set_, remove, chars, char
from .occupation import occupations
from .ability import abls, abl, asms, asm
from .augur import augurs, augur
from .tarot import tarot
from .soundboard import sound, shush

commands: FrozenSet[Any] = frozenset(
    (
        crit,
        init,
        inis,
        roll,
        new,
        char,
        chars,
        set_,
        remove,
        occupations,
        abls,
        abl,
        asms,
        asm,
        augurs,
        augur,
        tarot,
        sound,
        shush,
    )
)
