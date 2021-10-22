from typing import FrozenSet, Any

from .init import init, inis
from .roll import roll
from .character import new, update, remove
from .occupation import occupations
from .abilities import abls, abl, asms, asm
from .augur import augurs, augur
from .tarot import tarot

commands: FrozenSet[Any] = frozenset(
    (
        init,
        inis,
        roll,
        new,
        update,
        remove,
        occupations,
        abls,
        abl,
        asms,
        asm,
        augurs,
        augur,
        tarot,
    )
)
