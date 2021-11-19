from pathlib import Path
from typing import List, Dict
import json
import logging
import random

from discord.ext import commands  # type: ignore

from ...models.augur import AugurModel


_AUGURS: List[AugurModel] = []
_PATH: Path = Path(__file__).parent / "augurs.json"
if _PATH.exists():
    with open(_PATH, encoding="utf8") as fd:
        _AUGURS = [AugurModel(**a) for a in json.load(fd)["augurs"]]  # type: ignore
else:
    logging.warning("Unable to find %s", _PATH)

_AUGURS_DICT: Dict[int, AugurModel] = {aug.roll: aug for aug in _AUGURS}


def get_augurs() -> List[AugurModel]:
    return _AUGURS


def get_augur(roll: int) -> AugurModel:
    return _AUGURS_DICT[roll]


@commands.command()
async def augurs(ctx):
    await ctx.send(str(_AUGURS))


@commands.command()
async def augur(ctx):
    await ctx.send(str(random.choice(_AUGURS)))


@augurs.error
@augur.error
async def augur_error(ctx, error):
    await ctx.send(str(error), delete_after=5)
