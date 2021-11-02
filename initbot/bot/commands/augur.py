from pathlib import Path
from typing import List, Dict
import json
import random

from discord.ext import commands  # type: ignore

from ...models.augur import AugurModel


with open(Path(__file__).parent / "augurs.json", encoding="utf8") as fd:
    AUGURS: List[AugurModel] = [
        AugurModel(**a) for a in json.load(fd)["augurs"]
    ]  # type: ignore

AUGURS_DICT: Dict[int, AugurModel] = {aug.roll: aug for aug in AUGURS}


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
