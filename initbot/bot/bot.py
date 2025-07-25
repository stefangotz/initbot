from itertools import product

from discord.ext.commands import Bot
from discord import Intents

from .config import CFG
from .commands import commands
from ..state.factory import create_state_from_source
from ..models.roll import render_dice_rolls_in_text, contains_dice_rolls

intents = Intents.default()
intents.message_content = True

# pylint: disable=no-member
bot = Bot(command_prefix=tuple(CFG.command_prefixes.split(",")), intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    prefixes: tuple[str, ...] = tuple(
        p.strip() for p in CFG.command_prefixes.split(",")
    )
    command_names: tuple[str, ...] = tuple(cmd.name for cmd in commands)
    prefixed_commands: tuple[str, ...] = tuple(
        "".join(parts) for parts in product(prefixes, command_names)
    )
    is_command = any(
        message.content.startswith(prefixed_command)
        for prefixed_command in prefixed_commands
    )

    if not is_command and contains_dice_rolls(message.content):
        result_text = render_dice_rolls_in_text(message.content)
        if result_text != message.content:
            await message.channel.send(result_text)

    await bot.process_commands(message)


def run():
    for cmd in commands:
        bot.add_command(cmd)
    bot.initbot_state = create_state_from_source(CFG.state)  # type: ignore
    bot.run(CFG.token)
