from pathlib import Path
from typing import List, Dict
import logging
import random

from discord.ext import commands  # type: ignore

from ...data.augur import AugurData, AugursData


_AUGURS_DATA = AugursData(augurs=[])
_PATH: Path = Path(__file__).parent / "augurs.json"
if _PATH.exists():
    _AUGURS_DATA = AugursData.parse_file(_PATH)
else:
    logging.warning("Unable to find %s", _PATH)

_AUGURS_DICT: Dict[int, AugurData] = {aug.roll: aug for aug in _AUGURS_DATA.augurs}


def get_augurs() -> List[AugurData]:
    return _AUGURS_DATA.augurs


def get_augur(roll: int) -> AugurData:
    return _AUGURS_DICT[roll]


@commands.command()
async def augurs(ctx):
    """List all birth augurs that a 0-level character may start out with."""
    msg: str = "*Birth augurs modify certain character properties by the initial starting luck modifier of the character.*\n"
    for agr in _AUGURS_DATA.augurs:
        txt: str = f"{agr.roll}: {agr.description}\n"
        if len(msg) + len(txt) > 2000:
            await ctx.send(msg.rstrip())
            msg = ""
        msg += txt
    await ctx.send(msg.rstrip())


@commands.command()
async def augur(ctx):
    """Display a randomly chosen birth augur."""
    await ctx.send(str(random.choice(_AUGURS_DATA.augurs)))


@augurs.error
@augur.error
async def augur_error(ctx, error):
    await ctx.send(str(error), delete_after=5)
