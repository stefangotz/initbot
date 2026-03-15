import logging
import random
from typing import Any

from discord.ext import commands  # type: ignore

from .utils import send_in_parts


@commands.command()
async def augurs(ctx: Any) -> None:
    """List all birth augurs that a 0-level character may start out with."""
    parts: list[str] = [
        "*Birth augurs modify certain character properties by the initial starting luck modifier of the character.*\n"
    ] + [
        f"{agr.roll}: {agr.description}"
        for agr in ctx.bot.initbot_state.augurs.get_all()
    ]
    await send_in_parts(ctx, parts)


@commands.command()
async def augur(ctx: Any) -> None:
    """Display a randomly chosen birth augur."""
    await ctx.send(str(random.choice(ctx.bot.initbot_state.augurs.get_all())))


@augurs.error
@augur.error
async def augur_error(ctx: Any, error: Exception) -> None:
    logging.exception(ctx.command)
    await ctx.send(str(error), delete_after=5)
