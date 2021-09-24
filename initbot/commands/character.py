from dataclasses import dataclass
from dataclasses import asdict
from typing import List
import json
import random

from discord.ext import commands  # type: ignore

from .abilities import AbilityScore
from .roll import DieRoll
from .equipment import EQUIPMENT, Equipment
from .occupation import Occupation, OCCUPATIONS


@dataclass
class Character:
    name: str
    abilities: List[AbilityScore]
    hitpoints: int
    equipment: List[Equipment]
    occupation: Occupation
    exp: int


@commands.command()
async def cha(ctx, action: str):
    if action == "new":
        await cha_new(ctx)


async def cha_new(ctx):
    occupation = random.choice(OCCUPATIONS)
    abls = []
    character = Character(
        name="Jimmy",
        abilities=abls,
        hitpoints=DieRoll(4, 1).roll(),
        equipment=[
            Equipment("money", 1, DieRoll(12, 5).roll()),
            random.choice(EQUIPMENT),
        ]
        + occupation.goods,
        occupation=occupation,
        exp=0,
    )
    await ctx.send(json.dumps(asdict(character), indent=2, sort_keys=True))


@cha.error
async def character_error(ctx, error):
    await ctx.send(str(error))
