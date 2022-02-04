from typing import FrozenSet, Any

from .crit import crit
from .init import init, inis
from .roll import roll
from .character import new, set_, remove, chars, char
from .occupation import occupations
from .ability import abls, abl, mods, mod
from .augur import augurs, augur
from .tarot import tarot
from .cls import classes, cls

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
        mods,
        mod,
        augurs,
        augur,
        tarot,
        classes,
        cls,
    )
)
