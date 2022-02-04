import logging

from discord.ext import commands  # type: ignore


@commands.command()
async def classes(ctx):
    await ctx.send([cls.name for cls in ctx.bot.initbot_state.classes.get_all()])


@commands.command()
async def cls(ctx, name: str):
    await ctx.send(str(ctx.bot.initbot_state.classes.get_by_name(name))[:1000])


@classes.error
@cls.error
async def error(ctx, err):
    logging.exception(err)
    await ctx.send(str(err), delete_after=5)
