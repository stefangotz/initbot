from abc import ABC, abstractmethod
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Type
import random
import re


_NERD_DICE_ROLL_PATTERN = re.compile(
    r"^(([0-9]+)x)?([0-9]*)d([0-9]+)([+-][0-9]+)?$", re.IGNORECASE
)


def render_dice_rolls(words: Iterable[str]) -> str:
    return " ".join(map(_try_to_render_dice_roll, words))


def _try_to_render_dice_roll(word: str) -> str:
    for cls in _DICE_ROLL_CLASSES:
        try:
            return cls.create(word).roll()
        except ValueError:
            continue
    return word


class _DiceRoll(ABC):
    @abstractmethod
    def roll(self) -> str:
        pass

    @classmethod
    def is_valid_spec(cls: Type, spec: str) -> bool:
        try:
            return cls.create(spec) is not None
        except ValueError:
            return False

    @staticmethod
    @abstractmethod
    def create(spec: str) -> "_DiceRoll":
        pass


class IntDiceRoll(_DiceRoll, ABC):
    def roll(self) -> str:
        rolls = self.roll_all()
        if len(rolls) == 1:
            return str(rolls[0])
        return f"{sum(rolls)} ({str(rolls).strip('[]')})"

    @abstractmethod
    def roll_all(self) -> Sequence[int]:
        pass

    @abstractmethod
    def roll_one(self) -> int:
        pass


@dataclass(frozen=True)
class NerdDiceRoll(IntDiceRoll):
    sides: int
    dice: int = 1
    modifier: int = 0
    rolls: int = 1

    def roll_all(self) -> Sequence[int]:
        return tuple(self.roll_one() for _ in range(0, self.rolls))

    def roll_one(self) -> int:
        return (
            sum(random.randint(1, self.sides) for _ in range(0, self.dice))
            + self.modifier
        )

    def __str__(self):
        result = ""
        if self.rolls != 1:
            result += f"{self.rolls}x"
        if self.dice != 1:
            result += str(self.dice)
        result += f"d{self.sides}"
        if self.modifier != 0:
            if self.modifier > 0:
                result += "+"
            result += str(self.modifier)
        return result

    @staticmethod
    def create(spec: str) -> "NerdDiceRoll":
        match = _NERD_DICE_ROLL_PATTERN.match(spec)
        if match:
            args = {"sides": int(match.group(4))}
            if match.group(3):
                args["dice"] = int(match.group(3))
            if match.group(5):
                args["modifier"] = int(match.group(5))
            if match.group(2):
                args["rolls"] = int(match.group(2))
            return NerdDiceRoll(**args)
        raise ValueError(f"'{spec}' is not supported")


_DICE_ROLL_CLASSES: frozenset[Type[_DiceRoll]] = frozenset((NerdDiceRoll,))
