from pathlib import Path
from typing import List
import json
from discord.ext import commands  # type: ignore
from pydantic.dataclasses import dataclass

from ..utils import get_first_set_match
from .roll import DieRoll


@dataclass
class OccupationDI:
    rolls: List[int]
    name: str
    weapon: str
    goods: str


with open(Path(__file__).parent / "occupations.json", encoding="utf8") as fd:
    OCCUPATIONS: List[OccupationDI] = [
        OccupationDI(**o) for o in json.load(fd)["occupations"]  # type: ignore
    ]


def get_random_occupation() -> OccupationDI:
    roll: int = DieRoll(100).roll_one()
    return get_occupation(roll)


def get_occupation(roll: int) -> OccupationDI:
    return get_first_set_match(roll, OCCUPATIONS, lambda o: o.rolls)


@commands.command()
async def occupations(ctx):
    await ctx.send(str(OCCUPATIONS))


@occupations.error
async def occupations_error(ctx, error):
    await ctx.send(str(error), delete_after=5)
