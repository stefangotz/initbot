import random
from typing import Any

from discord.ext import commands  # type: ignore


@commands.command()
async def augurs(ctx: Any) -> None:
    """List all birth augurs that a 0-level character may start out with."""
    msg: str = "*Birth augurs modify certain character properties by the initial starting luck modifier of the character.*\n"
    for agr in ctx.bot.initbot_state.augurs.get_all():
        txt: str = f"{agr.roll}: {agr.description}\n"
        if len(msg) + len(txt) > 2000:
            await ctx.send(msg.rstrip())
            msg = ""
        msg += txt
    await ctx.send(msg.rstrip())


@commands.command()
async def augur(ctx: Any) -> None:
    """Display a randomly chosen birth augur."""
    await ctx.send(str(random.choice(ctx.bot.initbot_state.augurs.get_all())))


@augurs.error
@augur.error
async def augur_error(ctx: Any, error: Exception) -> None:
    await ctx.send(str(error), delete_after=5)
