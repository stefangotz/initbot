# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging

from discord.ext import commands

from initbot_chat.commands.utils import sync_player, web_configured
from initbot_core.config import CORE_CFG


@commands.command()
@web_configured
async def web(ctx: commands.Context) -> None:
    """Sends a personal, single-use web app login link via DM."""
    player = sync_player(ctx.bot.initbot_state, ctx)
    token = ctx.bot.initbot_state.web_login_tokens.create(discord_id=player.discord_id)
    if CORE_CFG.domain:
        url = f"https://{CORE_CFG.domain}/{CORE_CFG.web_url_path_prefix}/{token}/"
    else:
        url = f"http://localhost:8080/{CORE_CFG.web_url_path_prefix}/{token}/"
    await ctx.author.send(
        f"Your personal initiative tracker link (expires in 1 minute): {url}"
    )
    if ctx.guild is not None:
        await ctx.send("Check your DMs for your login link.", delete_after=5)


@web.error
async def web_error(ctx: commands.Context, error: commands.CommandError) -> None:
    logging.exception(ctx.command)
    await ctx.send(str(error), delete_after=5)
