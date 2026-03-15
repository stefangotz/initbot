import logging

from discord.ext import commands  # type: ignore

from .utils import send_in_parts


@commands.command()
async def occupations(ctx) -> None:
    """Lists all character occupations, including the starting weapon and goods they confer to new characters."""
    parts = (
        f"**{occ.name}** fights with *{occ.weapon}* and has *{occ.goods}*"
        for occ in ctx.bot.initbot_state.occupations.get_all()
    )
    await send_in_parts(ctx, parts)


@occupations.error
async def occupations_error(ctx, error) -> None:
    logging.exception(ctx.command)
    await ctx.send(str(error), delete_after=5)
