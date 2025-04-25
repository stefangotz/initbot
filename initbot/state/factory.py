from typing import Callable, Final

from .state import State
from .local import LocalState


class StateFactory:
    _FACTORIES: Final[frozenset[Callable[[str], State]]] = frozenset()

    @staticmethod
    def create(source: str) -> State:
        for factory in StateFactory._FACTORIES:
            try:
                return factory(source)
            except ValueError:
                pass
        return LocalState(source)
