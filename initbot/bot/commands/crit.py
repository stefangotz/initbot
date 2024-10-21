from discord.ext import commands  # type: ignore

from ...data.crit import CritTableData
from ...utils import get_first_set_match_or_over_under_flow


def _match(table: CritTableData, roll: int) -> str:
    return get_first_set_match_or_over_under_flow(
        roll, table.crits, lambda c: c.rolls
    ).effect


@commands.command()
async def crit(
    ctx,
    table: int = commands.parameter(description="The number of the crit table (1-4)"),
    roll: int = commands.parameter(description="What you rolled on your crit die"),
):
    """Shows the result of a roll on a crit table."""
    await ctx.send(_match(ctx.bot.initbot_state.crits.get_one(table), roll))


@crit.error
async def crit_error(ctx, error):
    await ctx.send(str(error), delete_after=5)
