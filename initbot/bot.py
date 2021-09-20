from discord.ext.commands import Bot  # type: ignore

from .config import CFG
from .commands.roll import roll

bot = Bot(command_prefix="$")


@bot.event
async def on_ready():
    print("Logged in as {0.user}".format(bot))


def run():
    bot.add_command(roll)
    bot.run(CFG.token)
