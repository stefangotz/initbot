import logging

from discord.ext import commands  # type: ignore


@commands.command()
async def classes(ctx):
    """Lists the names of all character classes."""
    await ctx.send([cls.name for cls in ctx.bot.initbot_state.classes.get_all()])


@commands.command()
async def cls(
    ctx,
    name: str = commands.parameter(
        description="The name of one of the character classes."
    ),
):
    """Shows details on a class."""
    await ctx.send(str(ctx.bot.initbot_state.classes.get_from_name(name))[:2000])


@classes.error
@cls.error
async def error(ctx, err):
    logging.exception(err)
    await ctx.send(str(err), delete_after=5)
