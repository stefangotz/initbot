from discord.ext.commands import Bot  # type: ignore

from .config import CFG
from .commands import commands

bot = Bot(command_prefix="$")


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


def run():
    for cmd in commands:
        bot.add_command(cmd)
    bot.run(CFG.token)
