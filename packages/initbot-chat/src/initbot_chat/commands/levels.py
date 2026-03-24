# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging

from discord.ext import commands


@commands.command()
async def levels(ctx: commands.Context) -> None:
    """Lists the XPs required to reach each character level"""
    xps = (0, 10, 50, 110, 190, 290, 410, 550, 710, 890, 1090)
    await ctx.send("\n".join(f"Level {lvl}: {xp} XP" for lvl, xp in enumerate(xps)))


@levels.error
async def levels_error(ctx: commands.Context, error: commands.CommandError) -> None:
    logging.exception(ctx.command)
    await ctx.send(str(error), delete_after=5)
