from pathlib import Path
from typing import List, Union, Iterable
import json
import random

from discord.ext import commands  # type: ignore
from pydantic.json import pydantic_encoder
from initbot.bot.utils import get_unique_prefix_match

from initbot.data.occupation import OccupationData

from ...data.ability import AbilityScoreData
from ...data.character import CharacterData, CharactersData
from .ability import get_abilities, get_mod
from .augur import AugurData, get_augur, get_augurs
from .roll import DieRoll
from .occupation import get_occupation, get_roll


_CHARACTERS_DATA: CharactersData = CharactersData(characters=[])  # type: ignore
_CHARACTER_DATAS: List[CharacterData] = _CHARACTERS_DATA.characters


class Character:
    def __init__(self, cdi: CharacterData):
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
    def ability_scores(self) -> List[AbilityScoreData]:
        return [
            AbilityScoreData(abl=abl, score=vars(self.cdi)[abl.name.lower()])
            for abl in get_abilities()
            if vars(self.cdi).get(abl.name.lower())
        ]

    def _get_ability_score(self, prefix: str) -> AbilityScoreData:
        return get_unique_prefix_match(
            prefix, self.ability_scores, lambda ability_score: ability_score.abl.name
        )

    @property
    def strength(self) -> Union[AbilityScoreData, None]:
        try:
            # TO DO: birth augur
            return self._get_ability_score("strength")
        except KeyError:
            pass
        return None

    @property
    def agility(self) -> Union[AbilityScoreData, None]:
        try:
            # TO DO: birth augur
            return self._get_ability_score("agility")
        except KeyError:
            pass
        return None

    @property
    def stamina(self) -> Union[AbilityScoreData, None]:
        try:
            # TO DO: birth augur
            return self._get_ability_score("stamina")
        except KeyError:
            pass
        return None

    @property
    def personality(self) -> Union[AbilityScoreData, None]:
        try:
            # TO DO: birth augur
            return self._get_ability_score("personality")
        except KeyError:
            pass
        return None

    @property
    def intelligence(self) -> Union[AbilityScoreData, None]:
        try:
            # TO DO: birth augur
            return self._get_ability_score("intelligence")
        except KeyError:
            pass
        return None

    @property
    def luck(self) -> Union[AbilityScoreData, None]:
        try:
            return self._get_ability_score("luck")
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
    def augur(self) -> Union[AugurData, None]:
        if self.cdi.augur is not None:
            return get_augur(self.cdi.augur)
        return None

    @property
    def occupation(self) -> Union[OccupationData, None]:
        if self.cdi.occupation is not None:
            return get_occupation(self.cdi.occupation)
        return None


def characters() -> List[Character]:
    return [Character(cdi) for cdi in _CHARACTER_DATAS]


def from_tokens(
    tokens: Iterable[str], user: str, create: bool = False
) -> CharacterData:
    name: str = " ".join(tokens)
    return from_str(name, user, create)


def from_str(name: str, user: str, create: bool = False) -> CharacterData:
    if name:
        return from_name(name, create, user)
    return from_user(user)


def from_name(
    name: str, create: bool = False, user: Union[str, None] = None
) -> CharacterData:
    try:
        return get_unique_prefix_match(name, _CHARACTER_DATAS, lambda cdi: cdi.name)
    except KeyError as err:
        if create and user:
            cdi: CharacterData = CharacterData(name=name, user=user)  # type: ignore
            _CHARACTER_DATAS.append(cdi)
            return cdi
        raise KeyError(f"Unable to find character with name '{name}'") from err


def from_user(user: str) -> CharacterData:
    return get_unique_prefix_match(user, _CHARACTER_DATAS, lambda cdi: cdi.user)


def normalize_name(name: str) -> str:
    return name.lower().replace(" ", "_")


def store_characters():
    with open(
        Path(__file__).parent / "characters.json", "w", encoding="UTF8"
    ) as file_desc:
        json.dump(_CHARACTERS_DATA, file_desc, default=pydantic_encoder)


def load_characters():
    path = Path(__file__).parent / "characters.json"
    if path.exists():
        global _CHARACTERS_DATA  # pylint: disable=global-statement
        _CHARACTERS_DATA = CharactersData.parse_file(path)
        global _CHARACTER_DATAS  # pylint: disable=global-statement
        _CHARACTER_DATAS = _CHARACTERS_DATA.characters


@commands.command()
async def new(ctx, name: str):
    occupation_roll: int = get_roll()
    occupation: OccupationData = get_occupation(occupation_roll)
    luck: int = DieRoll(6, 3).roll_one()
    cdi = CharacterData(
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
        augur=random.choice(get_augurs()).roll,
    )
    _CHARACTER_DATAS.append(cdi)
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
    cdi: CharacterData = from_tokens(name_tokens, ctx.author.display_name)
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
    cdi: CharacterData = from_tokens(args, ctx.author.display_name)
    _CHARACTER_DATAS.remove(cdi)
    store_characters()
    await ctx.send(f"Removed character {cdi.name}", delete_after=3)


@commands.command()
async def chars(ctx):
    """Displays all characters known to the bot."""
    txt: str = ", ".join([f"**{cdi.name}** (_{cdi.user}_)" for cdi in _CHARACTER_DATAS])
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
    cdi: CharacterData = from_tokens(args, ctx.author.display_name)
    await ctx.send(json.dumps(json.loads(cdi.json()), indent=4, sort_keys=True))


@new.error
@set_.error
@remove.error
@chars.error
@char.error
async def char_error(ctx, error):
    await ctx.send(str(error), delete_after=5)


load_characters()
