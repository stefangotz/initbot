from dataclasses import dataclass
from typing import List
import random
import re

from discord.ext import commands  # type: ignore

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
        return self.dice * random.randint(1, self.sides) + self.modifier

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


@commands.command(usage="dice")
async def roll(ctx, txt: str):
    """Rolls dice and returns the result.

    The *dice* to roll can be, for example, d20, 2d6, or d8+2.
    This follows the usual notation [dice]d{sides}[+/-mod] to say what kind of die to roll (how many sides), how many of those to roll, and how much bonus to add (or subtract).

    To make the same roll several times in a row and get each result separately, add [rolls]x, so for example, 3x1d6+1.
    This returns, for example, 5, 7, 2."""
    if DieRoll.is_die_roll(txt):
        dice = die_roll(txt)
        roll_result = dice.roll_all()
        if dice.rolls == 1:
            string = str(roll_result[0])
        else:
            string = str(roll_result).strip("[]")
        await ctx.send(f"{ctx.author.display_name} rolled **{string}** on {dice}")


@roll.error
async def roll_error(ctx, error):
    await ctx.send(str(error), delete_after=5)
