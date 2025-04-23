from typing import Callable, Final

from .local import LocalState
from .sql import SqlState
from .state import State


class StateFactory:
    _FACTORIES: Final[frozenset[Callable[[str], State]]] = frozenset(
        (SqlState.create_with_existing_sqlite_or_fail,)
    )

    @staticmethod
    def create(source: str) -> State:
        for factory in StateFactory._FACTORIES:
            try:
                return factory(source)
            except ValueError:
                pass
        return LocalState(source)
