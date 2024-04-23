from typing import List
import logging
from discord.ext import commands  # type: ignore

from initbot.models.roll import NerdDiceRoll
from .character import CharacterData


@commands.command()
async def luck(ctx, *args: str):
    """Performs a luck check.

    The character needs their luck attribute to be set for this command to work.
    To set it, use the command `$set CharacterName luck 10`.

    The command accepts an optional character name and optional dice to roll.

    If the Discord user manages only a single character, the character name is optional and can be ommitted: `$luck`
    If the Discord user manages more than one character, the character name is required: `$luck Mediocre Mel`

    The character name can be an abbreviation.
    For example, if the full name of a character is "Mediocre Mel", then typing "med" is sufficient: `$luck med`
    That's as long as no other character name starts with "med".

    The *dice* to roll can be, for example, d20, 2d6, or d8+2.
    This follows the usual notation [dice]d{sides}[+/-mod] to say what kind of die to roll (how many sides), how many of those to roll, and how much bonus to add (or subtract).
    If the dice are omitted from the command, a d20 is assumed.
    """
    name: List[str] = []
    die: str = "d20"
    if args and NerdDiceRoll.is_valid_spec(args[-1]):
        die = args[-1]
        name = list(args[0:-1])
    else:
        name = list(args)
    cdi: CharacterData = ctx.bot.initbot_state.characters.get_from_tokens(
        name, ctx.author.name
    )
    if cdi.luck is not None:
        roll = NerdDiceRoll.create(die).roll_one()
    else:
        raise ValueError(
            "Character doesn't have a luck attribute value. Set it with `$set {cdi.name} luck 10`"
        )

    if roll <= cdi.luck:
        result = "passed"
        diff = "under"
    else:
        result = "failed"
        diff = "over"
    await ctx.send(
        f"{cdi.name} rolled {roll} and {result} their luck check by {abs(roll - cdi.luck)} {diff} (their luck is {cdi.luck} ({ctx.bot.initbot_state.abilities.get_mod_from_score(cdi.luck).mod}))"
    )


@luck.error
async def handle_error(ctx, error):
    logging.exception(ctx.command)
    await ctx.send(str(error), delete_after=5)
