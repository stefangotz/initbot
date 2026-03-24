# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging

from discord.ext import commands

from initbot_core.data.crit import CritTableData
from initbot_core.utils import get_first_set_match_or_over_under_flow


def _match(table: CritTableData, roll: int) -> str:
    return get_first_set_match_or_over_under_flow(
        roll, table.crits, lambda c: c.rolls
    ).effect


@commands.command()
async def crit(
    ctx: commands.Context,
    table: int = commands.parameter(description="The number of the crit table (1-4)"),
    roll: int = commands.parameter(description="What you rolled on your crit die"),
) -> None:
    """Shows the result of a roll on a crit table."""
    await ctx.send(_match(ctx.bot.initbot_state.crits.get_one(table), roll))


@crit.error
async def crit_error(ctx: commands.Context, error: commands.CommandError) -> None:
    logging.exception(ctx.command)
    await ctx.send(str(error), delete_after=5)
