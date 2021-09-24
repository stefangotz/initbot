from dataclasses import dataclass
from typing import List
from discord.ext import commands  # type: ignore

from .equipment import Equipment


@dataclass
class Occupation:
    name: str
    weapon: str
    goods: List[Equipment]


OCCUPATIONS: List[Occupation] = [
    Occupation("Alchemist", "Staff", [Equipment("Oil flask")]),
    Occupation("Animal trainer", "Club", [Equipment("Pony")]),
]


@commands.command()
async def occupations(ctx):
    await ctx.send(str(OCCUPATIONS))


@occupations.error
async def occupations_error(ctx, error):
    await ctx.send(str(error))
