from dataclasses import dataclass
from dataclasses import asdict
from typing import List, Union, Iterable
import json
import random

from discord.ext import commands  # type: ignore

from .abilities import ABILITIES, AbilityScore
from .augur import Augur, AUGURS_DICT, AUGURS
from .roll import DieRoll
from .equipment import EQUIPMENT, Equipment
from .occupation import OccupationDI, get_random_occupation


@dataclass
class CharacterDI:
    name: str
    user: str
    strength: Union[int, None] = None
    agility: Union[int, None] = None
    stamina: Union[int, None] = None
    personality: Union[int, None] = None
    intelligence: Union[int, None] = None
    luck: Union[int, None] = None
    initial_luck: Union[int, None] = None
    hit_points: Union[int, None] = None
    equipment: Union[List[Equipment], None] = None
    occupation: Union[OccupationDI, None] = None
    exp: Union[int, None] = None
    alignment: Union[str, None] = None
    initiative: Union[int, None] = None
    initiative_modifier: Union[int, None] = None
    hit_die: Union[int, None] = None
    augur: Union[int, None] = None


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
    def abilities(self) -> List[AbilityScore]:
        return [
            AbilityScore(abl, vars(self.cdi)[abl.name.lower()])
            for abl in ABILITIES
            if vars(self.cdi).get(abl.name.lower())
        ]

    def _base_ability(self, prefix: str) -> AbilityScore:
        prefix = prefix.lower()
        candidates = [
            ab_score
            for ab_score in self.abilities
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
    def initiative(self) -> Union[int, None]:
        return self.cdi.initiative

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

    def initiative_comparison_value(self) -> int:
        if self.cdi.initiative is None:
            return -1

        ini = self.cdi.initiative * 1000000
        if self.agility is not None:
            ini += self.agility.score * 10000
        if self.hit_die is not None:
            ini += self.hit_die.sides * 100
        ini += random.randint(0, 99)

        return ini

    @property
    def augur(self) -> Union[Augur, None]:
        if self.cdi.augur is not None:
            return AUGURS_DICT[self.cdi.augur]
        return None


CHARACTER_DIS: List[CharacterDI] = []


def characters() -> List[Character]:
    return [Character(cdi) for cdi in CHARACTER_DIS]


def from_tokens(tokens: Iterable[str], user: str, create: bool = False) -> CharacterDI:
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
async def new(ctx, name: str):
    occupation: OccupationDI = get_random_occupation()
    luck: int = DieRoll(6, 3).roll_one()
    cdi = CharacterDI(
        name=name,
        user=ctx.author.display_name,
        strength=DieRoll(6, 3).roll_one(),
        agility=DieRoll(6, 3).roll_one(),
        stamina=DieRoll(6, 3).roll_one(),
        personality=DieRoll(6, 3).roll_one(),
        intelligence=DieRoll(6, 3).roll_one(),
        luck=luck,
        initial_luck=luck,
        hit_points=DieRoll(4, 1).roll_one(),
        equipment=[
            Equipment("money", 1, DieRoll(12, 5).roll_one()),
            random.choice(EQUIPMENT),
            occupation.goods,
        ],
        occupation=occupation,
        exp=0,
        alignment=random.choice(("Lawful", "Neutral", "Chaotic")),
        augur=random.choice(AUGURS).roll,
    )
    CHARACTER_DIS.append(cdi)
    txt: str = json.dumps(asdict(cdi), indent=2, sort_keys=True)
    for idx in range(0, len(txt), 1000):
        await ctx.send(txt[idx : idx + 1000])


@commands.command()
async def update(ctx, name: str, prop: str, val):
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


@commands.command(usage="[character name]")
async def remove(ctx, *args):
    """Remove a character from the bot.

    If the Discord user manages only a single character, the character name is optional and can be ommitted.
    If the Discord user manages more than one character, the character name is required.

    The character name can be an abbreviation.
    For example, if the full name of a character is "Mediocre Mel", then typing "Med" is sufficient.
    That's as long as no other character name starts with "Med"."""
    cdi: CharacterDI = from_tokens(args, ctx.author.display_name)
    CHARACTER_DIS.remove(cdi)


@new.error
@update.error
@remove.error
async def char_error(ctx, error):
    await ctx.send(str(error))
