import logging

from discord.ext import commands  # type: ignore

from ...models.roll import render_dice_rolls


@commands.command()
async def roll(ctx, *words):
    """Rolls dice and returns the result.

    The *dice* to roll can be, for example, d20, 2d6, or d8+2.
    This follows the usual notation [dice]d{sides}[+/-mod] to say what kind of die to roll (how many sides), how many of those to roll, and how much bonus to add (or subtract).

    To make the same roll several times in a row and get each result separately, add [rolls]x, so for example, 3x1d6+1.
    This generates a reply with a total and the individual rolls, for example, 14 (5, 7, 2).

    The bot just replaces anything that looks like a dice roll in your message with the result of the roll.
    For example, "roll d20+5 to attack the construct for 1d6+3 damage" will generate a reply like "Mediocre Mel rolled 15 to attack the construct for 7 damage".
    """
    await ctx.send(
        f"{ctx.author.display_name} rolled {render_dice_rolls(words)}",
    )


@roll.error
async def roll_error(ctx, error):
    logging.exception(ctx.command)
    await ctx.send(str(error), delete_after=5)
