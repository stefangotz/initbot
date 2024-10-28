import logging

from discord.ext import commands  # type: ignore


@commands.command()
async def occupations(ctx) -> None:
    """Lists all character occupations, including the starting weapon and goods they confer to new characters."""
    msg = ""
    for occ in ctx.bot.initbot_state.occupations.get_all():
        occ_str: str = (
            f"**{occ.name}** fights with *{occ.weapon}* and has *{occ.goods}*"
        )
        if len(msg) + 2 + len(occ_str) >= 2000:
            await ctx.send(msg)
            msg = ""
        if msg:
            msg += "\n"
        msg += occ_str
    if msg:
        await ctx.send(msg)


@occupations.error
async def occupations_error(ctx, error) -> None:
    logging.exception(ctx.command)
    await ctx.send(str(error), delete_after=5)
