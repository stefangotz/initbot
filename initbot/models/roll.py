from dataclasses import dataclass
from typing import List, Type
import random
import re


_DIE_PATTERN = re.compile(
    r"^(([0-9]+)x)?([0-9]*)[dw]([0-9]+)([+-][0-9]+)?$", re.IGNORECASE
)


class IntDiceRoll:
    def roll_all(self) -> List[int]:
        raise NotImplementedError()

    def roll_one(self) -> int:
        raise NotImplementedError()

    @classmethod
    def is_valid_spec(cls: Type, spec: str) -> bool:
        try:
            return cls.create(spec) is not None
        except ValueError:
            return False

    @staticmethod
    def create(spec: str) -> "IntDiceRoll":
        raise NotImplementedError()


@dataclass(frozen=True)
class DieRoll(IntDiceRoll):
    sides: int
    dice: int = 1
    modifier: int = 0
    rolls: int = 1

    def roll_all(self) -> List[int]:
        return [self.roll_one() for _ in range(0, self.rolls)]

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
    def create(spec: str) -> "DieRoll":
        match = _DIE_PATTERN.match(spec)
        if match:
            args = {"sides": int(match.group(4))}
            if match.group(3):
                args["dice"] = int(match.group(3))
            if match.group(5):
                args["modifier"] = int(match.group(5))
            if match.group(2):
                args["rolls"] = int(match.group(2))
            return DieRoll(**args)
        raise ValueError(f"'{spec}' is not supported")


def die_roll(spec: str) -> DieRoll:
    return DieRoll.create(spec)
