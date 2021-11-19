from pathlib import Path
from typing import List
import logging

from discord.ext import commands  # type: ignore

from ...models.occupation import OccupationModel, OccupationsModel
from ..utils import get_first_set_match
from .roll import DieRoll


_OCCUPATIONS_MODEL: OccupationsModel = OccupationsModel(occupations=[])
_PATH: Path = Path(__file__).parent / "occupations.json"
if _PATH.exists():
    _OCCUPATIONS_MODEL = OccupationsModel.parse_file(_PATH)
else:
    logging.warning("Unable to find %s", _PATH)


class Occupation:
    def __init__(self, model: OccupationModel):
        self.model: OccupationModel = model

    def __str__(self):
        return f"**{self.model.name}** fights with *{self.model.weapon}* and has *{self.model.goods}*"


_OCCUPATIONS: List[Occupation] = [
    Occupation(model) for model in _OCCUPATIONS_MODEL.occupations
]


def get_occupations() -> List[Occupation]:
    return _OCCUPATIONS


def get_random_occupation() -> OccupationModel:
    return get_occupation(get_roll())


def get_roll() -> int:
    return DieRoll(100).roll_one()


def get_occupation(roll: int) -> OccupationModel:
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
