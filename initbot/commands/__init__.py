from typing import FrozenSet, Any

from .init import init
from .roll import roll

commands: FrozenSet[Any] = frozenset((init, roll))
