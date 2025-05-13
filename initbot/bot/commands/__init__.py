from collections.abc import Set
from typing import Any

from .ability import abl, abls, mod, mods
from .augur import augur, augurs
from .character import char, chars, new, park, play, remove, set_
from .cls import classes, cls
from .crit import crit
from .init import inis, init
from .levels import levels
from .luck import luck
from .occupation import occupations
from .roll import roll
from .tarot import tarot

commands: Set[Any] = frozenset(
    (
        abl,
        abls,
        augur,
        augurs,
        char,
        chars,
        classes,
        cls,
        crit,
        inis,
        init,
        levels,
        luck,
        mod,
        mods,
        new,
        occupations,
        park,
        play,
        remove,
        roll,
        set_,
        tarot,
    )
)
