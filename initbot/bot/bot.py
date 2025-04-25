from discord.ext.commands import Bot
from discord import Intents

from .config import CFG
from .commands import commands
from ..state.factory import StateFactory

intents = Intents.default()
intents.message_content = True

bot = Bot(command_prefix=tuple(CFG.command_prefixes.split(",")), intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


def run():
    for cmd in commands:
        bot.add_command(cmd)
    bot.initbot_state = StateFactory.create(CFG.state)  # type: ignore
    bot.run(CFG.token)
