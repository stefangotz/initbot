from pathlib import Path
from typing import List, Union, Iterable
import json
import random

from discord.ext import commands  # type: ignore
from pydantic.json import pydantic_encoder

from initbot.models.occupation import OccupationModel

from ...models.ability import AbilityScoreModel
from ...models.character import CharacterModel, CharactersModel
from .ability import ABILITIES, get_mod
from .augur import AugurModel, AUGURS_DICT, AUGURS
from .roll import DieRoll
from .occupation import get_occupation, get_roll


CHARACTER_DIS: CharactersModel = CharactersModel(cdis=[])  # type: ignore
CDIS: List[CharacterModel] = CHARACTER_DIS.cdis


class Character:
    def __init__(self, cdi: CharacterModel):
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
    def abilities(self) -> List[AbilityScoreModel]:
        return [
            AbilityScoreModel(abl=abl, score=vars(self.cdi)[abl.name.lower()])
            for abl in ABILITIES
            if vars(self.cdi).get(abl.name.lower())
        ]

    def _base_ability(self, prefix: str) -> AbilityScoreModel:
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
    def strength(self) -> Union[AbilityScoreModel, None]:
        try:
            # TO DO: birth augur
            return self._base_ability("strength")
        except KeyError:
            pass
        return None

    @property
    def agility(self) -> Union[AbilityScoreModel, None]:
        try:
            # TO DO: birth augur
            return self._base_ability("agility")
        except KeyError:
            pass
        return None

    @property
    def stamina(self) -> Union[AbilityScoreModel, None]:
        try:
            # TO DO: birth augur
            return self._base_ability("stamina")
        except KeyError:
            pass
        return None

    @property
    def personality(self) -> Union[AbilityScoreModel, None]:
        try:
            # TO DO: birth augur
            return self._base_ability("personality")
        except KeyError:
            pass
        return None

    @property
    def intelligence(self) -> Union[AbilityScoreModel, None]:
        try:
            # TO DO: birth augur
            return self._base_ability("intelligence")
        except KeyError:
            pass
        return None

    @property
    def luck(self) -> Union[AbilityScoreModel, None]:
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
            return get_mod(self.agility.score)
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
    def augur(self) -> Union[AugurModel, None]:
        if self.cdi.augur is not None:
            return AUGURS_DICT[self.cdi.augur]
        return None

    @property
    def occupation(self) -> Union[OccupationModel, None]:
        if self.cdi.occupation is not None:
            return get_occupation(self.cdi.occupation)
        return None


def characters() -> List[Character]:
    return [Character(cdi) for cdi in CDIS]


def from_tokens(
    tokens: Iterable[str], user: str, create: bool = False
) -> CharacterModel:
    name: str = " ".join(tokens)
    return from_str(name, user, create)


def from_str(name: str, user: str, create: bool = False) -> CharacterModel:
    if name:
        return from_name(name, create, user)
    return from_user(user)


def from_name(
    name: str, create: bool = False, user: Union[str, None] = None
) -> CharacterModel:
    nrm: str = normalize_name(name)
    matches: List[CharacterModel] = [
        cdi for cdi in CDIS if normalize_name(cdi.name).startswith(nrm)
    ]
    if not matches and create and user:
        cdi: CharacterModel = CharacterModel(name=name, user=user)  # type: ignore
        CDIS.append(cdi)
        matches = [cdi]
    if len(matches) == 1:
        return matches[0]
    raise KeyError(f"Unable to find character with name '{name}'")


def from_user(user: str) -> CharacterModel:
    matches: List[CharacterModel] = [
        cdi for cdi in CDIS if normalize_name(cdi.user).startswith(user)
    ]
    if len(matches) == 1:
        return matches[0]
    raise KeyError(f"Unable to find character for user '{user}'")


def normalize_name(name: str) -> str:
    return name.lower().replace(" ", "_")


def store_characters():
    with open(
        Path(__file__).parent / "characters.json", "w", encoding="UTF8"
    ) as file_desc:
        json.dump(CHARACTER_DIS, file_desc, default=pydantic_encoder)


def load_characters():
    path = Path(__file__).parent / "characters.json"
    if path.exists():
        global CHARACTER_DIS  # pylint: disable=global-statement
        CHARACTER_DIS = CharactersModel.parse_file(path)
        global CDIS  # pylint: disable=global-statement
        CDIS = CHARACTER_DIS.cdis


@commands.command()
async def new(ctx, name: str):
    occupation_roll: int = get_roll()
    occupation: OccupationModel = get_occupation(occupation_roll)
    luck: int = DieRoll(6, 3).roll_one()
    cdi = CharacterModel(
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
            f"{DieRoll(12, 5).roll_one()}cp",
            # TO DO random.choice(EQUIPMENT),
            occupation.goods,
        ],
        occupation=occupation_roll,
        exp=0,
        alignment=random.choice(("Lawful", "Neutral", "Chaotic")),
        augur=random.choice(AUGURS).roll,
    )
    CDIS.append(cdi)
    store_characters()
    txt: str = cdi.json()
    for idx in range(0, len(txt), 1000):
        await ctx.send(txt[idx : idx + 1000])


@commands.command(name="set", usage="[character name] <attribute> <value>")
async def set_(ctx, *, txt):
    """Sets a character attribute.

    If the Discord user manages only a single character, the character name is optional and can be ommitted.
    If the Discord user manages more than one character, the character name is required.

    The character name can be an abbreviation.
    For example, if the full name of a character is "Mediocre Mel", then typing "Med" is sufficient.
    That's as long as no other character name starts with "Med".

    The same rule applies to the character attribute.
    You can list all character attributes with the `char` command.
    You do not need to spell out the full attribute name as the first few unique letters are good enough (e.g., "int" for "intelligence")"""
    tokens: List[str] = txt.split()
    if len(tokens) < 2:
        raise Exception(
            "You need to provide at least a character attribute and a value to set it to"
        )
    val = tokens[-1]
    attr = tokens[-2]
    name_tokens = tokens[0:-2]
    cdi: CharacterModel = from_tokens(name_tokens, ctx.author.display_name)
    attr = attr.lower()
    candidates: List[str] = []
    if attr in vars(cdi):
        candidates = [attr]
    else:
        candidates = [key for key in vars(cdi) if key.lower().startswith(attr)]
    if len(candidates) == 1:
        try:
            setattr(cdi, candidates[0], int(val))
        except ValueError:
            setattr(cdi, candidates[0], val)
        store_characters()
        await ctx.send(
            f"{cdi.name}'s {candidates[0]} is now {getattr(cdi, candidates[0])}",
            delete_after=3,
        )
    elif not candidates:
        await ctx.send(
            f"Character attribute {attr} isn't supported. Pick one of the following: {', '.join(vars(cdi).keys())}",
            delete_after=5,
        )
    else:
        await ctx.send(
            f"Character attribute {attr} is ambiguous. Pick one of the following: {', '.join(vars(cdi).keys())}",
            delete_after=5,
        )


@commands.command(usage="[character name]")
async def remove(ctx, *args):
    """Removes a character from the bot.

    If the Discord user manages only a single character, the character name is optional and can be ommitted.
    If the Discord user manages more than one character, the character name is required.

    The character name can be an abbreviation.
    For example, if the full name of a character is "Mediocre Mel", then typing "Med" is sufficient.
    That's as long as no other character name starts with "Med"."""
    cdi: CharacterModel = from_tokens(args, ctx.author.display_name)
    CDIS.remove(cdi)
    store_characters()
    await ctx.send(f"Removed character {cdi.name}", delete_after=3)


@commands.command()
async def chars(ctx):
    """Displays all characters known to the bot."""
    txt: str = ", ".join([f"**{cdi.name}** (_{cdi.user}_)" for cdi in CDIS])
    if not txt:
        txt = "No characters registered"
    await ctx.send(txt)


@commands.command()
async def char(ctx, *args):
    """Displays a character.

    If the Discord user manages only a single character, the character name is optional and can be ommitted.
    If the Discord user manages more than one character, the character name is required.

    The character name can be an abbreviation.
    For example, if the full name of a character is "Mediocre Mel", then typing "Med" is sufficient.
    That's as long as no other character name starts with "Med"."""
    cdi: CharacterModel = from_tokens(args, ctx.author.display_name)
    await ctx.send(json.dumps(json.loads(cdi.json()), indent=4, sort_keys=True))


@new.error
@set_.error
@remove.error
@chars.error
@char.error
async def char_error(ctx, error):
    await ctx.send(str(error), delete_after=5)


load_characters()
