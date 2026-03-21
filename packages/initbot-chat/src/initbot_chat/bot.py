# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from itertools import product

from discord import Intents
from discord.ext.commands import Bot

from initbot_chat.commands import commands
from initbot_chat.config import CFG
from initbot_core.models.roll import contains_dice_rolls, render_dice_rolls_in_text
from initbot_core.state.factory import create_state_from_source

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
    command_names: tuple[str, ...] = (*tuple(cmd.name for cmd in commands), "help")
    prefixed_commands: tuple[str, ...] = tuple(
        "".join(parts) for parts in product(prefixes, command_names)
    )
    is_command = any(
        message.content.startswith(prefixed_command)
        for prefixed_command in prefixed_commands
    )

    if len(
        message.content
    ) <= CFG.max_inline_roll_message_length and contains_dice_rolls(message.content):
        result_text = render_dice_rolls_in_text(message.content)
    else:
        result_text = message.content

    if is_command:
        if not message.content.split(sep=None, maxsplit=1)[0].endswith("roll"):
            message.content = result_text
        await bot.process_commands(message)
    elif result_text != message.content:
        await message.channel.send(result_text)


def run():
    for cmd in commands:
        bot.add_command(cmd)
    bot.initbot_state = create_state_from_source(CFG.state)  # type: ignore
    bot.run(CFG.token)
