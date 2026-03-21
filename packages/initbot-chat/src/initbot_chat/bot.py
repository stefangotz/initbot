# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
import sys
from itertools import product

from discord import Intents
from discord.abc import Messageable
from discord.ext import tasks
from discord.ext.commands import Bot

from initbot_chat.commands import commands
from initbot_chat.config import CFG
from initbot_core.models.roll import contains_dice_rolls, render_dice_rolls_in_text
from initbot_core.security import get_vulnerabilities
from initbot_core.state.factory import create_state_from_source

_log = logging.getLogger(__name__)

_IGNORE_SENTINEL = "ignore security vulnerabilities"

intents = Intents.default()
intents.message_content = True

# pylint: disable=no-member
bot = Bot(command_prefix=tuple(CFG.command_prefixes.split(",")), intents=intents)

_STARTUP_FAILED: bool = False


@tasks.loop(hours=24)
async def _vulnerability_check() -> None:
    vulns = await get_vulnerabilities()
    if not vulns:
        return
    for name, version, vuln_id in vulns:
        _log.warning("Security vulnerability in %s %s: %s", name, version, vuln_id)
    channel = bot.get_channel(int(CFG.alert_channel_id))
    if not isinstance(channel, Messageable):
        _log.warning(
            "Alert channel %s not found or not messageable", CFG.alert_channel_id
        )
        return
    await channel.send("This application needs to receive a security update.")


def _print_channel_diagnostic() -> None:
    print(
        "\nERROR: 'alert_channel_id' is not configured or refers to an unknown channel.\n"
        "\n"
        "The initbot chat application periodically scans its dependencies for known\n"
        "security vulnerabilities and posts a warning to a Discord channel when any\n"
        "are found. This allows users and server operators to take timely action\n"
        "before vulnerabilities can be exploited.\n"
        "\n"
        "Please set 'alert_channel_id' to the numeric ID of the channel where alerts\n"
        "should be posted. To find a channel ID in Discord: enable Developer Mode under\n"
        "User Settings → Advanced, then right-click the desired channel and select\n"
        "'Copy Channel ID'.\n"
        "\n"
        "If you intentionally want to disable security checks and accept the risk of\n"
        "running a bot with known vulnerabilities, set 'alert_channel_id' to the exact\n"
        f"string: {_IGNORE_SENTINEL!r}\n"
        "\n"
        "Available text channels on connected servers:\n"
    )
    for guild in bot.guilds:
        for channel in guild.text_channels:
            print(f"  {guild.name} / #{channel.name}: {channel.id}")
    print()


@bot.event
async def on_ready():
    global _STARTUP_FAILED  # pylint: disable=global-statement
    print(f"Logged in as {bot.user}")

    if CFG.alert_channel_id == _IGNORE_SENTINEL:
        _log.warning(
            "Security vulnerability checks are disabled. "
            "The bot will not alert users to known vulnerabilities."
        )
        return

    if not CFG.alert_channel_id or not isinstance(
        bot.get_channel(int(CFG.alert_channel_id)), Messageable
    ):
        _print_channel_diagnostic()
        _STARTUP_FAILED = True
        await bot.close()
        return

    if not _vulnerability_check.is_running():
        _vulnerability_check.start()


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
    if _STARTUP_FAILED:
        sys.exit(1)
