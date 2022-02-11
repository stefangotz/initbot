from typing import FrozenSet, Any

from .crit import crit
from .init import init, inis
from .roll import roll
from .character import new, set_, remove, chars, char, park, play
from .occupation import occupations
from .ability import abls, abl, mods, mod
from .augur import augurs, augur
from .tarot import tarot
from .cls import classes, cls

commands: FrozenSet[Any] = frozenset(
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
