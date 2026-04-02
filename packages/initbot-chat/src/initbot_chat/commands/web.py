# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging

from discord.ext import commands

from initbot_core.config import CORE_CFG


@commands.command()
async def web(ctx: commands.Context) -> None:
    """Replies with the URL of the web application."""
    await ctx.send(f"https://{CORE_CFG.domain}/{CORE_CFG.web_token}/")


@web.error
async def web_error(ctx: commands.Context, error: commands.CommandError) -> None:
    logging.exception(ctx.command)
    await ctx.send(str(error), delete_after=5)
