from typing import FrozenSet, Sequence
import random

from discord.ext import commands  # type: ignore

_STEMS: FrozenSet[str] = frozenset(
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
    await ctx.send(str(error))
