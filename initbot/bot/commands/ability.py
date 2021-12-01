from discord import Embed  # type: ignore
from discord.ext import commands  # type: ignore


@commands.command()
async def abls(ctx):
    """Lists the six character abilities and their descriptions."""
    embed = Embed(
        title="Abilities",
        description="**Luck**\n"
        + ctx.bot.initbot_state.abilities.get_from_prefix("Luck").description,
    )
    for ability in ctx.bot.initbot_state.abilities.get_all():
        if ability.name != "Luck":
            embed.add_field(name=ability.name, value=ability.description)
    await ctx.send(embed=embed)


@commands.command()
async def abl(ctx, name: str):
    await ctx.send(str(ctx.bot.initbot_state.abilities.get_from_prefix(name)))


@commands.command()
async def mods(ctx):
    await ctx.send(str(ctx.bot.initbot_state.abilities.get_mods()))


@commands.command()
async def mod(ctx, score: int):
    await ctx.send(str(ctx.bot.initbot_state.abilities.get_mod_from_score(score)))


@abls.error
@abl.error
@mods.error
@mod.error
async def handle_error(ctx, error):
    await ctx.send(str(error), delete_after=5)
