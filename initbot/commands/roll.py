from dataclasses import dataclass
import random
import re

from discord.ext import commands  # type: ignore

_DIE_PATTERN = re.compile(r"^([0-9]*)d([0-9]+)([+-][0-9]+)?$", re.IGNORECASE)


@dataclass
class DieRoll:
    sides: int
    dice: int = 1
    modifier: int = 0

    def roll(self):
        return self.dice * random.randint(1, self.sides) + self.modifier

    @staticmethod
    def is_die_roll(text: str) -> bool:
        return bool(_DIE_PATTERN.match(text))


def die_roll(text: str) -> DieRoll:
    match = _DIE_PATTERN.match(text)
    if match:
        ret = DieRoll(int(match.group(2)))
        if match.group(1):
            ret.dice = int(match.group(1))
        if match.group(3):
            ret.modifier = int(match.group(3))
        return ret
    raise TypeError()


@commands.command()
async def roll(ctx, txt: str):
    if DieRoll.is_die_roll(txt):
        result = die_roll(txt).roll()
        await ctx.send(
            f"You rolled **{result}** (_{ctx.message.content}_ - {ctx.author.display_name})"
        )
