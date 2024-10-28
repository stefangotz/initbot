import logging

from discord.ext import commands  # type: ignore

from ...models.roll import DieRoll, die_roll


@commands.command(usage="dice")
async def roll(ctx, txt: str):
    """Rolls dice and returns the result.

    The *dice* to roll can be, for example, d20, 2d6, or d8+2.
    This follows the usual notation [dice]d{sides}[+/-mod] to say what kind of die to roll (how many sides), how many of those to roll, and how much bonus to add (or subtract).

    To make the same roll several times in a row and get each result separately, add [rolls]x, so for example, 3x1d6+1.
    This returns, for example, 5, 7, 2."""
    if DieRoll.is_die_roll(txt):
        dice = die_roll(txt)
        roll_result = dice.roll_all()
        if dice.rolls == 1:
            string = str(roll_result[0])
            total = ""
        else:
            string = str(roll_result).strip("[]")
            total = f" ({sum(roll_result)} total) "
        await ctx.send(
            f"{ctx.author.display_name} rolled **{string}{total}** on {dice}"
        )


@roll.error
async def roll_error(ctx, error):
    logging.exception(ctx.command)
    await ctx.send(str(error), delete_after=5)
