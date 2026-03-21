# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
import random
from collections.abc import Sequence, Set

from discord.ext import commands  # type: ignore

_STEMS: Set[str] = frozenset(
    {
        "TheFool",
        "TheMagician",
        "TheHighPriestess",
        "TheEmpress",
        "TheEmperor",
        "TheHierophant",
        "TheLovers",
        "TheChariot",
        "Strength",
        "TheHermit",
        "WheelofFortune",
        "Justice",
        "TheHangedMan",
        "Death",
        "Temperance",
        "TheDevil",
        "TheTower",
        "TheStar",
        "TheMoon",
        "TheSun",
        "Judgement",
        "TheWorld",
    }
)
_URLS: Sequence[str] = tuple(
    f"https://randomtarotcard.com/{stem}.jpg" for stem in _STEMS
)


@commands.command()
async def tarot(ctx):
    """Displays a random tarot card."""
    await ctx.send(random.choice(_URLS))


@tarot.error
async def tarot_error(ctx, error):
    logging.exception(ctx.command)
    await ctx.send(str(error), delete_after=5)
