from dataclasses import dataclass
from dataclasses import asdict
from typing import List, Union
import json
import random

from discord.ext import commands  # type: ignore

from .abilities import AbilityScore, ABILITIES
from .roll import DieRoll
from .equipment import EQUIPMENT, Equipment
from .occupation import Occupation, OCCUPATIONS


@dataclass
class Character:
    name: str
    user: str
    abilities: Union[List[AbilityScore], None] = None
    hitpoints: Union[int, None] = None
    equipment: Union[List[Equipment], None] = None
    occupation: Union[Occupation, None] = None
    exp: Union[int, None] = None
    alignment: Union[str, None] = None


CHARACTERS: List[Character] = []


def from_tokens(tokens: List[str], user: str, create: bool = False) -> Character:
    name: str = " ".join(tokens)
    return from_str(name, user, create)


def from_str(name: str, user: str, create: bool = False) -> Character:
    if name:
        return from_name(name, create, user)
    return from_user(user)


def from_name(
    name: str, create: bool = False, user: Union[str, None] = None
) -> Character:
    nrm: str = normalize_name(name)
    matches: List[Character] = [
        cha for cha in CHARACTERS if normalize_name(cha.name).startswith(nrm)
    ]
    if not matches and create and user:
        matches = [Character(name, user)]
    if len(matches) == 1:
        return matches[0]
    raise KeyError(name)


def from_user(user: str) -> Character:
    matches: List[Character] = [
        cha for cha in CHARACTERS if normalize_name(cha.user).startswith(user)
    ]
    if len(matches) == 1:
        return matches[0]
    raise KeyError(user)


def normalize_name(name: str) -> str:
    return name.lower().replace(" ", "_")


@commands.command()
async def cha(ctx, action: str):
    if action == "new":
        await cha_new(ctx)


async def cha_new(ctx):
    occupation = random.choice(OCCUPATIONS)
    character = Character(
        name="Jimmy",
        user=ctx.author.display_name,
        abilities=[abl.roll() for abl in ABILITIES],
        hitpoints=DieRoll(4, 1).roll(),
        equipment=[
            Equipment("money", 1, DieRoll(12, 5).roll()),
            random.choice(EQUIPMENT),
        ]
        + occupation.goods,
        occupation=occupation,
        exp=0,
        alignment=random.choice(("Lawful", "Neutral", "Chaotic")),
    )
    CHARACTERS.append(character)
    txt: str = json.dumps(asdict(character), indent=2, sort_keys=True)
    for idx in range(0, len(txt), 1000):
        await ctx.send(txt[idx : idx + 1000])


@cha.error
async def character_error(ctx, error):
    await ctx.send(str(error))
