from dataclasses import dataclass
from typing import List
import random
import re


_DIE_PATTERN = re.compile(
    r"^(([0-9]+)x)?([0-9]*)d([0-9]+)([+-][0-9]+)?$", re.IGNORECASE
)


@dataclass
class DieRoll:
    sides: int
    dice: int = 1
    modifier: int = 0
    rolls: int = 1

    def roll_all(self) -> List[int]:
        return [self.roll_one() for _ in range(0, self.rolls)]

    def roll_one(self) -> int:
        return sum(
            random.randint(1, self.sides) + self.modifier for _ in range(0, self.dice)
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
    def is_die_roll(text: str) -> bool:
        return bool(_DIE_PATTERN.match(text))


def die_roll(text: str) -> DieRoll:
    match = _DIE_PATTERN.match(text)
    if match:
        ret = DieRoll(int(match.group(4)))
        if match.group(3):
            ret.dice = int(match.group(3))
        if match.group(5):
            ret.modifier = int(match.group(5))
        if match.group(2):
            ret.rolls = int(match.group(2))
        return ret
    raise TypeError()
