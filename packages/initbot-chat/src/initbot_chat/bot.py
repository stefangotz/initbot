# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
import sys
from collections import defaultdict
from collections.abc import Sequence
from itertools import product

import discord
from discord import Intents
from discord.abc import Messageable
from discord.ext import tasks
from discord.ext.commands import Bot

from initbot_chat.commands import commands
from initbot_chat.config import CFG
from initbot_core.config import CORE_CFG
from initbot_core.data.character import CharacterData, is_eligible_for_pruning
from initbot_core.models.roll import contains_dice_rolls, render_dice_rolls_in_text
from initbot_core.security import get_vulnerabilities, is_high_severity
from initbot_core.state.factory import create_state_from_source
from initbot_core.state.state import State

_log = logging.getLogger(__name__)

intents = Intents.default()
intents.message_content = True

# pylint: disable=no-member
bot = Bot(command_prefix=tuple(CFG.command_prefixes.split(",")), intents=intents)

_STARTUP_FAILED: bool = False


@tasks.loop(hours=24)
async def _vulnerability_check() -> None:
    vulns = await get_vulnerabilities()
    for name, version, vuln_id, severity in vulns:
        _log.warning(
            "Security vulnerability in %s %s: %s (severity: %s)",
            name,
            version,
            vuln_id,
            severity or "unknown",
        )
    if not any(is_high_severity(severity) for _, _, _, severity in vulns):
        return
    channel = bot.get_channel(int(CFG.alert_channel_id))
    if not isinstance(channel, Messageable):
        _log.warning(
            "Alert channel %s not found or not messageable", CFG.alert_channel_id
        )
        return
    await channel.send("This application needs to receive a security update.")


async def _notify_member(
    member: discord.Member, chars: Sequence[CharacterData], threshold: int, display: str
) -> None:
    names_list = "\n".join(f"- {c.name}" for c in chars)
    try:
        await member.send(
            f"Hi! The following characters you own haven't been used in over "
            f"{threshold} days:\n{names_list}\n\n"
            f"You have a few options:\n"
            f"1. Do nothing — you'll get another reminder next month.\n"
            f"2. Use `$prune` to remove all your unused characters.\n"
            f"3. Use `$remove <character name>` to remove a character.\n"
            f"4. Use `$touch <character name>` to mark a character as recently used "
            f"if you'd like to keep it."
        )
    except Exception:  # pylint: disable=broad-except
        _log.warning("Could not send pruning notification DM to %s", display)


async def _fetch_member(
    guilds: Sequence[discord.Guild], discord_id: int
) -> discord.Member | None:
    for guild in guilds:
        try:
            return await guild.fetch_member(discord_id)
        except (  # noqa: PERF203  # try/except per guild is intentional: skip 404, warn on other errors
            discord.NotFound
        ):
            continue
        except discord.HTTPException as exc:
            _log.warning(
                "HTTP error fetching member %d from %s: %s",
                discord_id,
                guild.name,
                exc,
            )
    return None


async def _send_pruning_notifications(
    guilds: Sequence[discord.Guild], state: State
) -> None:
    """Send pruning reminder DMs to all players with eligible characters."""
    threshold = CORE_CFG.prune_threshold_days
    by_player_id: dict[int, list] = defaultdict(list)
    for cdi in state.characters.get_all():
        if is_eligible_for_pruning(cdi, threshold):
            by_player_id[cdi.player_id].append(cdi)

    for player_id, chars in by_player_id.items():
        player = state.players.get_from_id(player_id)
        member = await _fetch_member(guilds, player.discord_id)
        if not member:
            _log.warning(
                "Could not find guild member for pruning notification: player_id=%d",
                player_id,
            )
            continue
        await _notify_member(member, chars, threshold, display=f"player_id={player_id}")


@tasks.loop(hours=24 * 30)
async def _pruning_notification() -> None:
    await _send_pruning_notifications(bot.guilds, bot.initbot_state)  # type: ignore


def _print_channel_diagnostic() -> None:
    print(
        "\nERROR: 'alert_channel_id' refers to an unknown channel.\n"
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
        "Available text channels on connected servers:\n"
    )
    for guild in bot.guilds:
        for channel in guild.text_channels:
            print(f"  {guild.name} / #{channel.name}: {channel.id}")
    print()


@bot.event
async def on_ready() -> None:
    global _STARTUP_FAILED  # pylint: disable=global-statement
    print(f"Logged in as {bot.user}")

    if not _pruning_notification.is_running():
        _pruning_notification.start()

    if not CFG.alert_channel_id:
        _log.warning(
            "Security vulnerability checks are disabled. "
            "The bot will not alert users to known vulnerabilities."
        )
        return

    if not isinstance(bot.get_channel(int(CFG.alert_channel_id)), Messageable):
        _print_channel_diagnostic()
        _STARTUP_FAILED = True
        await bot.close()
        return

    if not _vulnerability_check.is_running():
        _vulnerability_check.start()


@bot.event
async def on_message(message: discord.Message) -> None:
    if message.author == bot.user:
        return

    prefixes: tuple[str, ...] = tuple(
        p.strip() for p in CFG.command_prefixes.split(",")
    )
    command_names: tuple[str, ...] = tuple(bot.all_commands)
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
        command = (
            str(message.content).split(sep=None, maxsplit=1)[0].strip("".join(prefixes))
        )
        if command not in frozenset(("actions", "init_dice", "roll")):
            message.content = result_text
        await bot.process_commands(message)
    elif result_text != message.content:
        await message.channel.send(result_text)


def run() -> None:
    for cmd in commands:
        bot.add_command(cmd)
    bot.initbot_state = create_state_from_source(CFG.state)  # type: ignore
    bot.run(CFG.token)
    if _STARTUP_FAILED:
        sys.exit(1)
