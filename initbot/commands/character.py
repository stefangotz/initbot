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
class CharacterDI:
    name: str
    user: str
    # TO DO: make easy to set
    abilities: Union[List[AbilityScore], None] = None
    creation_luck: Union[AbilityScore, None] = None
    hit_points: Union[int, None] = None
    equipment: Union[List[Equipment], None] = None
    occupation: Union[Occupation, None] = None
    exp: Union[int, None] = None
    alignment: Union[str, None] = None
    initiative: Union[int, None] = None
    initiative_modifier: Union[int, None] = None
    hit_die: Union[int, None] = None


class Character:
    def __init__(self, cdi: CharacterDI):
        self.cdi = cdi

    @property
    def name(self) -> str:
        return self.cdi.name

    @name.setter
    def name(self, name: str):
        self.cdi.name = name

    @property
    def user(self) -> str:
        return self.cdi.user

    @user.setter
    def user(self, user: str):
        self.cdi.user = user

    @property
    def abilities(self) -> Union[List[AbilityScore], None]:
        return self.cdi.abilities

    @abilities.setter
    def abilities(self, abilities: List[AbilityScore]):
        self.cdi.abilities = abilities

    def _base_ability(self, prefix: str) -> AbilityScore:
        prefix = prefix.lower()
        if self.cdi.abilities:
            candidates = [
                ab_score
                for ab_score in self.cdi.abilities
                if ab_score.abl.name.lower().startswith(prefix)
            ]
            if len(candidates) == 1:
                return candidates[0]
        raise KeyError(prefix)

    @property
    def strength(self) -> Union[AbilityScore, None]:
        try:
            # TO DO: birth augur
            return self._base_ability("strength")
        except KeyError:
            pass
        return None

    @property
    def agility(self) -> Union[AbilityScore, None]:
        try:
            # TO DO: birth augur
            return self._base_ability("agility")
        except KeyError:
            pass
        return None

    @property
    def stamina(self) -> Union[AbilityScore, None]:
        try:
            # TO DO: birth augur
            return self._base_ability("stamina")
        except KeyError:
            pass
        return None

    @property
    def personality(self) -> Union[AbilityScore, None]:
        try:
            # TO DO: birth augur
            return self._base_ability("personality")
        except KeyError:
            pass
        return None

    @property
    def intelligence(self) -> Union[AbilityScore, None]:
        try:
            # TO DO: birth augur
            return self._base_ability("intelligence")
        except KeyError:
            pass
        return None

    @property
    def luck(self) -> Union[AbilityScore, None]:
        try:
            return self._base_ability("luck")
        except KeyError:
            pass
        return None

    @property
    def hit_points(self) -> Union[int, None]:
        return self.cdi.hit_points

    @hit_points.setter
    def hit_points(self, hit_points: int):
        self.cdi.hit_points = hit_points

    @property
    def initiative_modifier(self) -> Union[int, None]:
        if self.cdi.initiative_modifier is None and self.agility is not None:
            # TO DO: modify by class (warrior gets +level)
            # TO DO: modify by birth augur
            # roll is also modified by two-handed weapon (d16)
            return self.agility.mod
        return None

    @initiative_modifier.setter
    def initiative_modifier(self, ini_mod: int):
        self.cdi.initiative_modifier = ini_mod

    @property
    def hit_die(self) -> Union[DieRoll, None]:
        if self.cdi.hit_die is not None:
            return DieRoll(self.cdi.hit_die)
        # TO DO: derive from class
        return None

    def initiative_tie_breakers(self) -> List[int]:
        breakers: List[int] = []
        if self.agility is not None:
            breakers.append(self.agility.score)
            if self.hit_die is not None:
                breakers.append(self.hit_die.sides)
        return breakers


CHARACTER_DIS: List[CharacterDI] = []


def from_tokens(tokens: List[str], user: str, create: bool = False) -> CharacterDI:
    name: str = " ".join(tokens)
    return from_str(name, user, create)


def from_str(name: str, user: str, create: bool = False) -> CharacterDI:
    if name:
        return from_name(name, create, user)
    return from_user(user)


def from_name(
    name: str, create: bool = False, user: Union[str, None] = None
) -> CharacterDI:
    nrm: str = normalize_name(name)
    matches: List[CharacterDI] = [
        cdi for cdi in CHARACTER_DIS if normalize_name(cdi.name).startswith(nrm)
    ]
    if not matches and create and user:
        cdi: CharacterDI = CharacterDI(name, user)
        CHARACTER_DIS.append(cdi)
        matches = [cdi]
    if len(matches) == 1:
        return matches[0]
    raise KeyError(name)


def from_user(user: str) -> CharacterDI:
    matches: List[CharacterDI] = [
        cdi for cdi in CHARACTER_DIS if normalize_name(cdi.user).startswith(user)
    ]
    if len(matches) == 1:
        return matches[0]
    raise KeyError(user)


def normalize_name(name: str) -> str:
    return name.lower().replace(" ", "_")


@commands.command()
async def char_new(ctx):
    occupation: Occupation = random.choice(OCCUPATIONS)
    abilities: List[AbilityScore] = [abl.roll() for abl in ABILITIES]
    cdi = CharacterDI(
        name="Jimmy",
        user=ctx.author.display_name,
        abilities=abilities,
        creation_luck=[abl for abl in abilities if abl.abl.name == "Luck"][0],
        hit_points=DieRoll(4, 1).roll(),
        equipment=[
            Equipment("money", 1, DieRoll(12, 5).roll()),
            random.choice(EQUIPMENT),
        ]
        + occupation.goods,
        occupation=occupation,
        exp=0,
        alignment=random.choice(("Lawful", "Neutral", "Chaotic")),
    )
    CHARACTER_DIS.append(cdi)
    txt: str = json.dumps(asdict(cdi), indent=2, sort_keys=True)
    for idx in range(0, len(txt), 1000):
        await ctx.send(txt[idx : idx + 1000])


@commands.command()
async def char_set(ctx, name: str, prop: str, val):
    cdi: CharacterDI = from_str(name, ctx.author.display_name)
    prop = prop.lower()
    candidates: List[str] = []
    if prop in vars(cdi):
        candidates = [prop]
    else:
        candidates = [key for key in vars(cdi) if key.lower().startswith(prop)]
    if len(candidates) == 1:
        setattr(cdi, candidates[0], val)
        await ctx.send(f"Set {name}'s {prop} to {val}")
    elif not candidates:
        await ctx.send(
            f"Character property {prop} isn't supported. Pick one of the following: {', '.join(vars(cdi).keys())}"
        )
    else:
        await ctx.send(
            f"Character property {prop} is ambiguous. Pick one of the following: {', '.join(vars(cdi).keys())}"
        )


@char_new.error
@char_set.error
async def char_error(ctx, error):
    await ctx.send(str(error))
