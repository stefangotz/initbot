# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging

from discord.ext import commands

from initbot_chat.commands.utils import occupations_required, send_in_parts


@commands.command()
@occupations_required
async def occupations(ctx: commands.Context) -> None:
    """Lists all character occupations, including the starting weapon and goods they confer to new characters."""
    parts = (
        f"**{occ.name}** fights with *{occ.weapon}* and has *{occ.goods}*"
        for occ in ctx.bot.initbot_state.occupations.get_all()
    )
    await send_in_parts(ctx, parts)


@occupations.error
async def occupations_error(
    ctx: commands.Context, error: commands.CommandError
) -> None:
    logging.exception(ctx.command)
    await ctx.send(str(error), delete_after=5)
