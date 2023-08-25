from discord.ext import commands  # type: ignore


@commands.command()
async def levels(ctx):
    """Lists the XPs required to reach each character level"""
    xps = (0, 10, 50, 110, 190, 290, 410, 550, 710, 890, 1090)
    await ctx.send("\n".join(f"Level {lvl}: {xp} XP" for lvl, xp in enumerate(xps)))


@levels.error
async def levels_error(ctx, error):
    await ctx.send(str(error), delete_after=5)
