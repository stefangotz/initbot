from typing import List

from discord.ext import commands  # type: ignore

from ..utils import is_int
from .character import from_tokens, CharacterDI


@commands.command()
async def init(ctx, *, name_and_initiative: str):
    tokens: List[str] = name_and_initiative.split()
    if len(tokens) == 0:
        raise Exception("Provide an optional name and an init value")
    if len(tokens) > 4:
        raise Exception("Too long")
    if not is_int(tokens[-1]):
        raise Exception("Provide initiative value")
    char_data: CharacterDI = from_tokens(
        tokens[0:-1], ctx.author.display_name, create=True
    )

    await ctx.send(name_and_initiative + " " + str(len(tokens)) + " " + char_data.name)


@init.error
async def init_error(ctx, error):
    await ctx.send(str(error))
