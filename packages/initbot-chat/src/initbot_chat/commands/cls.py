# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging

from discord.ext import commands


@commands.command()
async def classes(ctx: commands.Context) -> None:
    """Lists the names of all character classes."""
    await ctx.send(str([cls.name for cls in ctx.bot.initbot_state.classes.get_all()]))


@commands.command()
async def cls(
    ctx: commands.Context,
    name: str = commands.parameter(
        description="The name of one of the character classes."
    ),
) -> None:
    """Shows details on a class. The class name must be given in full (unlike most other commands, prefix matching is not supported)."""
    await ctx.send(str(ctx.bot.initbot_state.classes.get_from_name(name))[:2000])


@classes.error
@cls.error
async def error(ctx: commands.Context, err: commands.CommandError) -> None:
    logging.exception(ctx.command)
    await ctx.send(str(err), delete_after=5)
