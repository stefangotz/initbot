# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
import time
from collections.abc import Iterable
from datetime import datetime

from discord.ext import commands

from initbot_chat.commands.utils import player_name, send_in_parts, sync_player
from initbot_core.config import CORE_CFG
from initbot_core.data.character import (
    CharacterData,
    is_eligible_for_pruning,
)
from initbot_core.models.roll import NerdDiceRoll
from initbot_core.state.state import State


def characters(state: State) -> Iterable[CharacterData]:
    return state.characters.get_all()


@commands.command(usage="[character name] <dice spec>")
async def init_dice(ctx: commands.Context, *args: str) -> None:
    """Sets the initiative dice specification for a character.

    The dice spec defines how initiative is rolled for this character when the
    *init* command is used without an explicit value.

    Examples:
    - `$init_dice d20` — roll a plain d20
    - `$init_dice d20+3` — roll d20 and add 3
    - `$init_dice Alfalfa d20+3` — set spec for the named character

    Setting the dice spec clears any previously rolled initiative value.

    If the Discord user manages only a single character, the character name is
    optional and can be omitted.  If there is no character with the given name,
    a new character with that name is created.

    The character name can be an abbreviation.
    """
    player = sync_player(ctx.bot.initbot_state, ctx)
    tokens = list(args)
    if not tokens:
        raise ValueError(
            "Please provide a dice spec, e.g. `$init_dice d20+3` or `$init_dice Alfalfa d20+3`"
        )

    spec = tokens[-1]
    name = tokens[:-1]

    try:
        NerdDiceRoll.create(spec)
    except ValueError as exc:
        raise ValueError(
            f"'{spec}' is not a valid dice spec. Use a format like d20, d20+3, or 2d6-1."
        ) from exc

    cdi: CharacterData = ctx.bot.initbot_state.characters.get_from_tokens(
        name, create=len(name) > 0, player_id=player.id
    )
    cdi.initiative_dice = spec
    cdi.initiative = None
    cdi.last_used = int(time.time())
    ctx.bot.initbot_state.characters.update_and_store(cdi)
    await ctx.send(f"{cdi.name}'s initiative dice is now {spec}", delete_after=3)


@commands.command(usage="[character name]")
async def remove(ctx: commands.Context, *args: str) -> None:
    """Removes a character from the bot.

    If the Discord user manages only a single character, the character name is optional and can be omitted.
    If the Discord user manages more than one character, the character name is required.

    The character name can be an abbreviation.
    For example, if the full name of a character is "Mediocre Mel", then typing "Med" is sufficient.
    That's as long as no other character name starts with "Med"."""
    player = sync_player(ctx.bot.initbot_state, ctx)
    cdi: CharacterData = ctx.bot.initbot_state.characters.get_from_tokens(
        args, player_id=player.id
    )
    ctx.bot.initbot_state.character_actions.remove_all_for_character(cdi.name)
    ctx.bot.initbot_state.characters.remove_and_store(cdi)
    await ctx.send(f"Removed character {cdi.name}", delete_after=3)


@commands.command()
async def chars(ctx: commands.Context) -> None:
    """Displays all characters known to the bot."""
    sync_player(ctx.bot.initbot_state, ctx)
    state = ctx.bot.initbot_state
    parts = (
        f"- {idx}: **{cdi.name}** (_{player_name(state, cdi)}_)\n"
        for idx, cdi in enumerate(state.characters.get_all())
    )
    await send_in_parts(ctx, parts)


@commands.command()
async def char(ctx: commands.Context, *args: str) -> None:
    """Displays a character.

    If the Discord user manages only a single character, the character name is optional and can be omitted.
    If the Discord user manages more than one character, the character name is required.

    The character name can be an abbreviation.
    For example, if the full name of a character is "Mediocre Mel", then typing "Med" is sufficient.
    That's as long as no other character name starts with "Med"."""
    player = sync_player(ctx.bot.initbot_state, ctx)
    state = ctx.bot.initbot_state
    cdi: CharacterData = state.characters.get_from_tokens(args, player_id=player.id)
    last_used_str = (
        datetime.fromtimestamp(cdi.last_used).strftime("%Y-%m-%d %H:%M")
        if cdi.last_used is not None
        else "never"
    )
    lines = [
        f"**{cdi.name}** ({player_name(state, cdi)})",
        f"Initiative dice: {cdi.initiative_dice or '(not set)'}",
        f"Initiative: {cdi.initiative if cdi.initiative is not None else '(not rolled)'}",
        f"Last used: {last_used_str}",
    ]
    await ctx.send("\n".join(lines))


@commands.command(usage="[all_players]")
async def unused(ctx: commands.Context, *args: str) -> None:
    """Lists characters that haven't been used in a while and might be worth removing.

    By default, this command only lists the requesting player's own characters.
    Pass 'all_players' to list eligible characters belonging to any player."""
    player = sync_player(ctx.bot.initbot_state, ctx)
    state = ctx.bot.initbot_state
    show_all = "all_players" in args
    threshold = CORE_CFG.prune_threshold_days
    eligible = [
        cdi
        for cdi in state.characters.get_all()
        if is_eligible_for_pruning(cdi, threshold)
        and (show_all or cdi.player_id == player.id)
    ]
    if not eligible:
        await ctx.send("You don't seem to have any unused characters.", delete_after=5)
        return
    parts = (f"- **{cdi.name}** (_{player_name(state, cdi)}_)\n" for cdi in eligible)
    await send_in_parts(ctx, parts)


@commands.command(usage="[all_players]")
async def prune(ctx: commands.Context, *args: str) -> None:
    """Removes all characters that haven't been used in a while.

    By default, only prunes the requesting player's own characters.
    Pass 'all_players' to prune unused characters belonging to any player.
    Replies with the names of the pruned characters."""
    player = sync_player(ctx.bot.initbot_state, ctx)
    show_all = "all_players" in args
    threshold = CORE_CFG.prune_threshold_days
    to_prune = [
        cdi
        for cdi in ctx.bot.initbot_state.characters.get_all()
        if is_eligible_for_pruning(cdi, threshold)
        and (show_all or cdi.player_id == player.id)
    ]
    for cdi in to_prune:
        ctx.bot.initbot_state.character_actions.remove_all_for_character(cdi.name)
        ctx.bot.initbot_state.characters.remove_and_store(cdi)
    if not to_prune:
        await ctx.send("No characters to prune.", delete_after=5)
        return
    await ctx.send("Pruned: " + ", ".join(cdi.name for cdi in to_prune))


@commands.command(usage="[character name] [character name ...]")
async def touch(ctx: commands.Context, *args: str) -> None:
    """Marks one or more characters as recently used, so they are not considered for pruning.

    Each argument is treated as a separate character name or abbreviation.
    If the Discord user manages only a single character, the character name is optional.

    The character name can be an abbreviation.
    For example, if the full name of a character is "Mediocre Mel", then typing "Med" is sufficient.
    That's as long as no other character name starts with "Med"."""
    player = sync_player(ctx.bot.initbot_state, ctx)
    tokens: tuple = args if args else ((),)
    touched = []
    for token in tokens:
        name_arg = (token,) if token else ()
        cdi: CharacterData = ctx.bot.initbot_state.characters.get_from_tokens(
            name_arg, player_id=player.id
        )
        cdi.last_used = int(time.time())
        ctx.bot.initbot_state.characters.update_and_store(cdi)
        touched.append(cdi.name)
    await ctx.send(
        "Marked as recently used: " + ", ".join(touched),
        delete_after=3,
    )


@init_dice.error
@remove.error
@chars.error
@char.error
@unused.error
@prune.error
@touch.error
async def char_error(ctx: commands.Context, error: commands.CommandError) -> None:
    logging.exception(ctx.command)
    await ctx.send(str(error), delete_after=5)
