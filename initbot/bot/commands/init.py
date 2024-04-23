from datetime import datetime
from typing import List
import logging

from discord import Embed  # type: ignore
from discord.ext import commands
from initbot.models.roll import NerdDiceRoll  # type: ignore

from ...utils import is_int
from .character import CharacterData, Character, characters


@commands.command(usage="[character name] initiative *or* initiative [character name]")
async def init(ctx, *args: str) -> None:
    """Sets the initiative of a character.

    This sets a character's iniative to the specified *initiative*, primarily so that the *inis* command ranks the character by its initiative.

    If the Discord user manages only a single character, the character name is optional and can be ommitted: `$init 10`
    If the Discord user manages more than one character, the character name is required: `$init Mediocre Mel 10`

    The character name can be an abbreviation.
    For example, if the full name of a character is "Mediocre Mel", then typing "med" is sufficient: `$init med 10`
    That's as long as no other character name starts with "med".

    If there is no character with the given name, a new character with that name is created.

    The bot can roll initiative itself with this command.
    To make that work, the character needs to be set up with all the attributes that impact iniative.
    In most cases, one only needs to set their agility: `$set Mediocre Mel agility 10`.
    But the class, birth augur, and other attributes may influence initiative as well.
    With that set up, make the bot automatically roll initiative simply by omitting the initative value: `$init Mediocre Mel`

    Thus, in the shortest (and most common case), one can simply use the command `$init` by itself to automatically roll and set a character's initiative.
    """
    tokens: List[str] = list(args)
    if len(tokens) > 4:
        raise ValueError("Too long")
    if len(tokens) == 0:
        initiative = None
        name = []
    elif is_int(tokens[-1]):
        initiative = int(tokens[-1])
        name = tokens[0:-1]
    elif is_int(tokens[0]):
        initiative = int(tokens[0])
        name = tokens[1:]
    else:
        initiative = None
        name = tokens
    cdi: CharacterData = ctx.bot.initbot_state.characters.get_from_tokens(
        name, ctx.author.name, create=len(name) > 0
    )
    if initiative is None:
        char = Character(cdi, ctx.bot.initbot_state)
        if char.initiative_modifier is not None:
            initiative = NerdDiceRoll(20, modifier=char.initiative_modifier).roll_one()
        else:
            raise ValueError(
                "Character has no initiative modifier. Set their agility and other character attributes that affect initiative with the $set command."
            )

    cdi.initiative = initiative
    cdi.initiative_time = int(datetime.now().timestamp())

    ctx.bot.initbot_state.characters.update_and_store(cdi)

    suffix = ""
    if not cdi.active:
        suffix = (
            " (note that this character is not currently active; you may want to activate this character with the 'play' command or maybe you meant a"
            " different character?)"
        )
    await ctx.send(
        f"{cdi.name}'s initiative is now {cdi.initiative}" + suffix, delete_after=3
    )


@commands.command()
async def inis(ctx) -> None:
    """Lists characters in initiative order.

    Use the *init* command to set the initiative value of a character.
    Use the *remove* command to remove a character.

    Initiative order is evaluated as per the rules.
    However, this works only as far as the necessary information is available for a character.
    For example, if two characters have the same initiative value and their Agility scores are known, the tie is broken based on that.
    However, if their Agility scores are not set, the tie on the initiative value is broken randomly.
    """

    def discard_characters_with_old_initiative_times(char: Character):
        return (
            char.initiative_time is not None
            and char.initiative_time > int(datetime.now().timestamp()) - 24 * 3600
        )

    def ini_comparator(char: Character):
        return char.initiative_comparison_value()

    sorted_characters = sorted(
        filter(
            discard_characters_with_old_initiative_times,
            characters(ctx.bot.initbot_state),
        ),
        key=ini_comparator,
        reverse=True,
    )
    desc: str = "\n".join(
        f"{char.initiative}: **{char.name}** (*{char.user}*)"
        for char in sorted_characters
    )
    embed = Embed(title="Initiative Order", description=desc)
    await ctx.send(embed=embed)


@inis.error
@init.error
async def init_error(ctx, error) -> None:
    logging.exception(ctx.command)
    await ctx.send(str(error), delete_after=5)
