from discord.ext.commands import Bot  # type: ignore

from .config import CONF
from .commands import commands

sound_bot = Bot(command_prefix="$")


@sound_bot.event
async def on_ready():
    print(f"Logged in as {sound_bot.user}")


def run():
    for com in commands:
        sound_bot.add_command(com)
    sound_bot.run(CONF.bot_token)
