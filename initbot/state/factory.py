from collections.abc import Mapping, Set
from itertools import chain
from typing import Callable, Final

from .local import LocalState
from .sql import SqlState
from .state import State


_STATE_CLASSES: Final[Set[type[State]]] = frozenset({LocalState, SqlState})
_FACTORIES: Final[Mapping[str, Callable[[str], State]]] = dict(
    chain.from_iterable(
        ((state_type, cls) for state_type in cls.get_supported_state_types())
        for cls in _STATE_CLASSES
    )
)


def create_state_from_source(source: str) -> State:
    name = source.split(":", maxsplit=1)[0]
    try:
        return _FACTORIES[name](source)
    except KeyError as exc:
        raise ValueError(
            f"Unknown kind of data store: {name}; supported: {_FACTORIES.keys()}"
        ) from exc
