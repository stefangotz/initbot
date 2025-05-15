from discord.ext.commands import Bot
from discord import Intents

from .config import CFG
from .commands import commands
from ..state.factory import create_state_from_source

intents = Intents.default()
intents.message_content = True

# pylint: disable=no-member
bot = Bot(command_prefix=tuple(CFG.command_prefixes.split(",")), intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


def run():
    for cmd in commands:
        bot.add_command(cmd)
    bot.initbot_state = create_state_from_source(CFG.state)  # type: ignore
    bot.run(CFG.token)
