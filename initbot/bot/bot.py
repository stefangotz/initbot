from discord.ext.commands import Bot
from discord import Intents

from .config import CFG
from .commands import commands
from ..state.local import LocalState

intents = Intents.default()
intents.message_content = True

bot = Bot(command_prefix="$", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


def run():
    for cmd in commands:
        bot.add_command(cmd)
    bot.initbot_state = LocalState()  # type: ignore
    bot.run(CFG.token)
