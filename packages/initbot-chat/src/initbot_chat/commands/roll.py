# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging

from discord.ext import commands

from initbot_core.models.roll import render_dice_rolls


@commands.command()
async def roll(ctx: commands.Context, *words: str) -> None:
    """Rolls dice and returns the result.

    The *dice* to roll can be, for example, d20, 2d6, or d8+2.
    This follows the usual notation [dice]d{sides}[+/-mod] to say what kind of die to roll (how many sides), how many of those to roll, and how much bonus to add (or subtract).

    You can combine different dice types with + or -: d20+d8 rolls both and adds them, d20+d8+d6 rolls all three, and 2d6+d4+3 rolls the mixed group and adds 3.

    To evaluate an expression several times and see each result separately, add [rolls]x: 3xd6 rolls d6 three times, and 2x(d20+d8) evaluates d20+d8 twice.
    This generates a reply showing each result and the total, for example, 4+13=17.

    The bot just replaces anything that looks like a dice roll in your message with the result of the roll.
    For example, "roll d20+5 to attack the construct for 1d6+3 damage" will generate a reply like "Mediocre Mel rolled 15 to attack the construct for 7 damage".
    """
    await ctx.send(
        f"{ctx.author.display_name} rolled {render_dice_rolls(words)}",
    )


@roll.error
async def roll_error(ctx: commands.Context, error: commands.CommandError) -> None:
    logging.exception(ctx.command)
    await ctx.send(str(error), delete_after=5)
