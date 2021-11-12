from pathlib import Path
from typing import List
from discord.ext import commands  # type: ignore

from ...models.occupation import OccupationModel, OccupationsModel
from ..utils import get_first_set_match
from .roll import DieRoll


OCCUPATIONS_MODEL: OccupationsModel = OccupationsModel.parse_file(
    Path(__file__).parent / "occupations.json"
)
OCCUPATIONS: List[OccupationModel] = OCCUPATIONS_MODEL.occupations


def get_random_occupation() -> OccupationModel:
    return get_occupation(get_roll())


def get_roll() -> int:
    return DieRoll(100).roll_one()


def get_occupation(roll: int) -> OccupationModel:
    return get_first_set_match(roll, OCCUPATIONS, lambda o: o.rolls)


@commands.command()
async def occupations(ctx):
    await ctx.send(str(OCCUPATIONS))


@occupations.error
async def occupations_error(ctx, error):
    await ctx.send(str(error), delete_after=5)
