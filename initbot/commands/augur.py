from pathlib import Path
from typing import List, Dict
import json
import random
from pydantic.dataclasses import dataclass

from discord.ext import commands  # type: ignore


@dataclass
class Augur:
    description: str
    roll: int


with open(Path(__file__).parent / "augur.json", encoding="utf8") as fd:
    AUGURS: List[Augur] = [Augur(**a) for a in json.load(fd)["augurs"]]  # type: ignore

AUGURS_DICT: Dict[int, Augur] = {aug.roll: aug for aug in AUGURS}


@commands.command()
async def augurs(ctx):
    await ctx.send(str(AUGURS))


@commands.command()
async def augur(ctx):
    await ctx.send(str(random.choice(AUGURS)))


@augurs.error
@augur.error
async def augur_error(ctx, error):
    await ctx.send(str(error), delete_after=5)
