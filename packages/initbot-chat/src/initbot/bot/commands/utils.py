from typing import Iterable

from discord.ext.commands import Context


async def send_in_parts(
    ctx: Context,
    parts: Iterable[str],
) -> None:
    msg: str = ""
    for txt in parts:
        if len(msg) + len(txt) >= 2000:
            await ctx.send(msg)
            msg = ""
        msg += "\n" + txt
    if msg:
        await ctx.send(msg)
