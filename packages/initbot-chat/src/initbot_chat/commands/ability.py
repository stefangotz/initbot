# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging

from discord import Embed
from discord.ext import commands

from initbot_chat.commands.utils import abilities_required, send_in_parts


@commands.command()
@abilities_required
async def abls(ctx: commands.Context) -> None:
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
@abilities_required
async def abl(
    ctx: commands.Context,
    name: str = commands.parameter(
        description="The name of the ability to get details on. A prefix (say, 'str' instead of 'strength') is good enough."
    ),
) -> None:
    """Displays the description for the given ability."""
    await ctx.send(str(ctx.bot.initbot_state.abilities.get_from_prefix(name)))


@commands.command()
@abilities_required
async def mods(ctx: commands.Context) -> None:
    """Lists all ability scores, their corresponding modifiers and, for wizards, the spell count and maximum spell level implied by intelligence."""
    parts = [
        f"{m.score}: {m.mod:+d} modifier, {m.spells} spells, max spell level {m.max_spell_level}"
        for m in ctx.bot.initbot_state.abilities.get_mods()
    ]
    await send_in_parts(ctx, parts)


@commands.command()
@abilities_required
async def mod(
    ctx: commands.Context,
    score: int = commands.parameter(description="An ability score (3-18)."),
) -> None:
    """Shows details for an ability score. It lists the corresponding modifier and, for wizards, the spell count and maximum spell level implied by intelligence."""
    m = ctx.bot.initbot_state.abilities.get_mod_from_score(score)
    await ctx.send(
        f"{m.score}: {m.mod:+d} modifier, {m.spells} spells, max spell level {m.max_spell_level}"
    )


@abls.error
@abl.error
@mods.error
@mod.error
async def handle_error(ctx: commands.Context, error: commands.CommandError) -> None:
    logging.exception(ctx.command)
    await ctx.send(str(error), delete_after=5)
