from typing import Any, List
import json
import random

from discord.ext import commands  # type: ignore

from ...data.character import CharacterData
from ...data.occupation import OccupationData
from ...models.character import Character
from ...models.roll import DieRoll
from ...state.state import State


def characters(state: State) -> List[Character]:
    return [
        Character(char_data, state)
        for char_data in state.characters.get_all()
        if char_data.active
    ]


@commands.command()
async def new(ctx: Any, name: str) -> None:
    """Creates a new character with a given name.

    The core attributes of the character are rolled randomly as per standard character creation rules.
    """
    occupation_roll: int = DieRoll(100).roll_one()
    occupation: OccupationData = ctx.bot.initbot_state.occupations.get_from_roll(
        occupation_roll
    )
    luck: int = DieRoll(6, 3).roll_one()
    cdi = CharacterData(
        name=name,
        user=ctx.author.name,
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
        augur=random.choice(ctx.bot.initbot_state.augurs.get_all()).roll,
    )
    ctx.bot.initbot_state.characters.add_and_store(cdi)
    txt: str = cdi.model_dump_json()
    for idx in range(0, len(txt), 1000):
        await ctx.send(txt[idx : idx + 1000])


@commands.command(name="set", usage="[character name] <attribute> <value>")
async def set_(ctx: Any, *, txt: str) -> None:
    """Sets a character attribute.

    If the Discord user manages only a single character, the character name is optional and can be ommitted.
    If the Discord user manages more than one character, the character name is required.

    The character name can be an abbreviation.
    For example, if the full name of a character is "Mediocre Mel", then typing "Med" is sufficient.
    That's as long as no other character name starts with "Med".

    The same rule applies to the character attribute.
    You can list all character attributes with the `char` command.
    You do not need to spell out the full attribute name as the first few unique letters are good enough (e.g., "int" for "intelligence")
    """
    tokens: List[str] = txt.split()
    if len(tokens) < 2:
        raise ValueError(
            "You need to provide at least a character attribute and a value to set it to"
        )
    val = tokens[-1]
    attr = tokens[-2]
    name_tokens = tokens[0:-2]
    cdi: CharacterData = ctx.bot.initbot_state.characters.get_from_tokens(
        name_tokens, ctx.author.name
    )
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
        ctx.bot.initbot_state.characters.update_and_store(cdi)
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
async def remove(ctx: Any, *args: str) -> None:
    """Removes a character from the bot.

    If the Discord user manages only a single character, the character name is optional and can be ommitted.
    If the Discord user manages more than one character, the character name is required.

    The character name can be an abbreviation.
    For example, if the full name of a character is "Mediocre Mel", then typing "Med" is sufficient.
    That's as long as no other character name starts with "Med"."""
    cdi: CharacterData = ctx.bot.initbot_state.characters.get_from_tokens(
        args, ctx.author.name
    )
    ctx.bot.initbot_state.characters.remove_and_store(cdi)
    await ctx.send(f"Removed character {cdi.name}", delete_after=3)


@commands.command()
async def chars(ctx: Any) -> None:
    """Displays all characters known to the bot."""
    txt: str = ", ".join(
        [
            f"{idx}: **{cdi.name}** (_{cdi.user}_)"
            for idx, cdi in enumerate(ctx.bot.initbot_state.characters.get_all())
        ]
    )
    if not txt:
        txt = "No characters registered"
    await ctx.send(txt)


@commands.command()
async def char(ctx: Any, *args: str) -> None:
    """Displays a character.

    If the Discord user manages only a single character, the character name is optional and can be ommitted.
    If the Discord user manages more than one character, the character name is required.

    The character name can be an abbreviation.
    For example, if the full name of a character is "Mediocre Mel", then typing "Med" is sufficient.
    That's as long as no other character name starts with "Med"."""
    cdi: CharacterData = ctx.bot.initbot_state.characters.get_from_tokens(
        args, ctx.author.name
    )
    await ctx.send(
        json.dumps(json.loads(cdi.model_dump_json()), indent=4, sort_keys=True)
    )


@commands.command()
async def park(ctx: Any, *args: str) -> None:
    """Deactivates a character so it is no longer included in the initiative order.

    If the Discord user manages only a single character, the character name is optional and can be ommitted.
    If the Discord user manages more than one character, the character name is required.

    The character name can be an abbreviation.
    For example, if the full name of a character is "Mediocre Mel", then typing "Med" is sufficient.
    That's as long as no other character name starts with "Med"."""
    cdi: CharacterData = ctx.bot.initbot_state.characters.get_from_tokens(
        args, ctx.author.name
    )
    cdi.active = False
    ctx.bot.initbot_state.characters.update_and_store(cdi)
    await ctx.send(f"{cdi.name} is now inactive", delete_after=3)


@commands.command()
async def play(ctx: Any, *args: str) -> None:
    """Activates a character deactivated with the 'park' command so it is included in the initiative order again.

    If the Discord user manages only a single character, the character name is optional and can be ommitted.
    If the Discord user manages more than one character, the character name is required.

    The character name can be an abbreviation.
    For example, if the full name of a character is "Mediocre Mel", then typing "Med" is sufficient.
    That's as long as no other character name starts with "Med"."""
    cdi: CharacterData = ctx.bot.initbot_state.characters.get_from_tokens(
        args, ctx.author.name
    )
    cdi.active = True
    ctx.bot.initbot_state.characters.update_and_store(cdi)
    await ctx.send(f"{cdi.name} is now active", delete_after=3)


@new.error
@set_.error
@remove.error
@chars.error
@char.error
@park.error
@play.error
async def char_error(ctx, error):
    await ctx.send(str(error), delete_after=5)
