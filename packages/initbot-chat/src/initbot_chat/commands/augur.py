# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
import random

from discord.ext import commands

from initbot_chat.commands.utils import send_in_parts


@commands.command()
async def augurs(ctx: commands.Context) -> None:
    """List all birth augurs that a 0-level character may start out with."""
    parts: list[str] = [
        "*Birth augurs modify certain character properties by the initial starting luck modifier of the character.*\n"
    ] + [
        f"{agr.roll}: {agr.description}"
        for agr in ctx.bot.initbot_state.augurs.get_all()
    ]
    await send_in_parts(ctx, parts)


@commands.command()
async def augur(ctx: commands.Context) -> None:
    """Display a randomly chosen birth augur."""
    await ctx.send(str(random.choice(ctx.bot.initbot_state.augurs.get_all())))


@augurs.error
@augur.error
async def augur_error(ctx: commands.Context, error: commands.CommandError) -> None:
    logging.exception(ctx.command)
    await ctx.send(str(error), delete_after=5)
