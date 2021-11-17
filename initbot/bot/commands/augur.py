from pathlib import Path
from typing import List, Dict
import json
import logging
import random

from discord.ext import commands  # type: ignore

from ...models.augur import AugurModel


AUGURS: List[AugurModel] = []
PATH: Path = Path(__file__).parent / "augurs.json"
if PATH.exists():
    with open(PATH, encoding="utf8") as fd:
        AUGURS = [AugurModel(**a) for a in json.load(fd)["augurs"]]  # type: ignore
else:
    logging.warning("Unable to find %s", PATH)

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
