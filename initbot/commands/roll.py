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

    def __init__(self, text: str):
        match = _DIE_PATTERN.match(text)
        if match:
            self.sides = int(match.group(2))
            if match.group(1):
                self.dice = int(match.group(1))
            if match.group(3):
                self.modifier = int(match.group(3))

    def roll(self):
        return self.dice * random.randint(1, self.sides) + self.modifier

    @staticmethod
    def is_die_roll(text: str) -> bool:
        return bool(_DIE_PATTERN.match(text))


@commands.command()
async def roll(ctx, txt: str):
    if DieRoll.is_die_roll(txt):
        result = DieRoll(txt).roll()
        await ctx.send(
            f"You rolled **{result}** (_{ctx.message.content}_ - {ctx.author.display_name})"
        )
