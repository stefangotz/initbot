from typing import List

from discord import Embed  # type: ignore
from discord.ext import commands  # type: ignore

from ...utils import is_int
from .character import (
    from_tokens,
    CharacterData,
    Character,
    characters,
    store_characters,
)


@commands.command(usage="[character name] initiative *or* initiative [character name]")
async def init(ctx, *, name_and_initiative: str):
    """Sets the initiative of a character.

    This sets a character's iniative to the specified *initiative*, primarily so that the *inis* command ranks the character by its initiative.

    If the Discord user manages only a single character, the character name is optional and can be ommitted.
    If the Discord user manages more than one character, the character name is required.

    The character name can be an abbreviation.
    For example, if the full name of a character is "Mediocre Mel", then typing "Med" is sufficient.
    That's as long as no other character name starts with "Med".

    If there is no character with the given name, a new character with that name is created.
    """
    tokens: List[str] = name_and_initiative.split()
    if len(tokens) == 0:
        raise Exception("Provide an optional name and an init value")
    if len(tokens) > 4:
        raise Exception("Too long")
    if is_int(tokens[-1]):
        initiative = int(tokens[-1])
        name = tokens[0:-1]
    elif is_int(tokens[0]):
        initiative = int(tokens[0])
        name = tokens[1:]
    else:
        raise Exception("Provide initiative value")
    cdi: CharacterData = from_tokens(name, ctx.author.display_name, create=True)
    cdi.initiative = initiative

    store_characters()

    await ctx.send(f"{cdi.name}'s initiative is now {cdi.initiative}", delete_after=3)


@commands.command()
async def inis(ctx):
    """Lists characters in initiative order.

    Use the *init* command to set the initiative value of a character.
    Use the *remove* command to remove a character.

    Initiative order is evaluated as per the rules.
    However, this works only as far as the necessary information is available for a character.
    For example, if two characters have the same initiative value and their Agility scores are known, the tie is broken based on that.
    However, if their Agility scores are not set, the tie on the initiative value is broken randomly."""

    def ini_comparator(char: Character):
        return char.initiative_comparison_value()

    sorted_characters = sorted(
        characters(ctx.bot.initbot_state), key=ini_comparator, reverse=True
    )
    desc: str = "\n".join(
        f"{char.initiative}: **{char.name}** (*{char.user}*)"
        for char in sorted_characters
    )
    embed = Embed(title="Initiative Order", description=desc)
    await ctx.send(embed=embed)


@inis.error
@init.error
async def init_error(ctx, error):
    await ctx.send(str(error), delete_after=5)
