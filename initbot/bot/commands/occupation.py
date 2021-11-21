from pathlib import Path
from typing import List
import logging

from discord.ext import commands  # type: ignore

from ...data.occupation import OccupationData, OccupationsData
from ..utils import get_first_set_match
from .roll import DieRoll


_OCCUPATIONS_DATA: OccupationsData = OccupationsData(occupations=[])
_PATH: Path = Path(__file__).parent / "occupations.json"
if _PATH.exists():
    _OCCUPATIONS_DATA = OccupationsData.parse_file(_PATH)
else:
    logging.warning("Unable to find %s", _PATH)


class Occupation:
    def __init__(self, data: OccupationData):
        self.data: OccupationData = data

    def __str__(self):
        return f"**{self.data.name}** fights with *{self.data.weapon}* and has *{self.data.goods}*"


_OCCUPATIONS: List[Occupation] = [
    Occupation(data) for data in _OCCUPATIONS_DATA.occupations
]


def get_occupations() -> List[Occupation]:
    return _OCCUPATIONS


def get_random_occupation() -> OccupationData:
    return get_occupation(get_roll())


def get_roll() -> int:
    return DieRoll(100).roll_one()


def get_occupation(roll: int) -> OccupationData:
    return get_first_set_match(roll, get_occupations, lambda o: o.rolls)


@commands.command()
async def occupations(ctx):
    """Lists all character occupations, including the starting weapon and goods they confer to new characters."""
    msg = ""
    for occ in get_occupations():
        occ_str: str = str(occ)
        if len(msg) + 2 + len(occ_str) >= 2000:
            await ctx.send(msg)
            msg = ""
        if msg:
            msg += "\n"
        msg += occ_str
    if msg:
        await ctx.send(msg)


@occupations.error
async def occupations_error(ctx, error):
    await ctx.send(str(error), delete_after=5)
