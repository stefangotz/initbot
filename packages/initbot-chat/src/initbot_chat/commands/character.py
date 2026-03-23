# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import dataclasses
import logging
import random
from collections.abc import Iterable, Sequence
from typing import Any

from discord.ext import commands

from initbot_chat.commands.utils import send_in_parts
from initbot_core.config import CORE_CFG
from initbot_core.data.character import CharacterData, is_eligible_for_pruning
from initbot_core.data.occupation import OccupationData
from initbot_core.models.character import Character
from initbot_core.models.roll import NerdDiceRoll
from initbot_core.state.state import State


def characters(state: State) -> Iterable[Character]:
    return (
        Character(char_data, state)
        for char_data in state.characters.get_all()
        if char_data.active
    )


@commands.command()
async def new(ctx: Any, name: str) -> None:
    """Creates a new character with a given name.

    The core attributes of the character are rolled randomly as per standard character creation rules:
    - Ability scores (strength, agility, stamina, personality, intelligence, luck): 3d6 each
    - Hit points: 1d4
    - Occupation: d100 on the occupation table
    - Alignment: randomly Lawful, Neutral, or Chaotic
    - Birth augur: randomly chosen from the augur table
    """
    occupation_roll: int = NerdDiceRoll(100).roll_one()
    occupation: OccupationData = ctx.bot.initbot_state.occupations.get_from_roll(
        occupation_roll
    )
    luck: int = NerdDiceRoll(6, 3).roll_one()
    cdi = CharacterData(
        name=name,
        user=ctx.author.name,
        strength=NerdDiceRoll(6, 3).roll_one(),
        agility=NerdDiceRoll(6, 3).roll_one(),
        stamina=NerdDiceRoll(6, 3).roll_one(),
        personality=NerdDiceRoll(6, 3).roll_one(),
        intelligence=NerdDiceRoll(6, 3).roll_one(),
        luck=luck,
        initial_luck=luck,
        hit_points=NerdDiceRoll(4, 1).roll_one(),
        equipment=(
            f"{NerdDiceRoll(12, 5).roll_one()}cp",
            # TO DO random.choice(EQUIPMENT),
            occupation.goods,
        ),
        occupation=occupation_roll,
        exp=0,
        alignment=random.choice(("Lawful", "Neutral", "Chaotic")),
        augur=random.choice(ctx.bot.initbot_state.augurs.get_all()).roll,
    )
    cdi = ctx.bot.initbot_state.characters.add_store_and_get(cdi)
    txt: str = str(cdi)
    for idx in range(0, len(txt), 1000):
        await ctx.send(txt[idx : idx + 1000])


@commands.command(name="set", usage="[character name] <attribute> <value>")
async def set_(ctx: Any, *, txt: str) -> None:
    """Sets a character attribute.

    If the Discord user manages only a single character, the character name is optional and can be omitted.
    If the Discord user manages more than one character, the character name is required.

    The character name can be an abbreviation.
    For example, if the full name of a character is "Mediocre Mel", then typing "Med" is sufficient.
    That's as long as no other character name starts with "Med".

    The same rule applies to the character attribute.
    You can list all character attributes with the `char` command.
    You do not need to spell out the full attribute name as the first few unique letters are good enough (e.g., "int" for "intelligence")
    """
    tokens = txt.split()
    if len(tokens) < 2:
        raise ValueError(
            "You need to provide at least a character attribute and a value to set it to"
        )
    val = tokens[-1]
    attr = tokens[-2]
    name_tokens = tokens[0:-2]
    cdi: CharacterData = ctx.bot.initbot_state.characters.get_from_tokens(
        name_tokens, ctx.author.name
    )
    attr = attr.lower()
    char_fields = [
        f.name for f in dataclasses.fields(CharacterData) if f.name != "last_used"
    ]
    candidates: Sequence[str] = []
    if attr in char_fields:
        candidates = [attr]
    else:
        candidates = [key for key in char_fields if key.lower().startswith(attr)]
    if len(candidates) == 1:
        try:
            setattr(cdi, candidates[0], int(val))
        except ValueError:
            setattr(cdi, candidates[0], val)
        ctx.bot.initbot_state.characters.update_and_store(cdi)
        await ctx.send(
            f"{cdi.name}'s {candidates[0]} is now {getattr(cdi, candidates[0])}",
            delete_after=3,
        )
    elif not candidates:
        await ctx.send(
            f"Character attribute {attr} isn't supported. Pick one of the following: {', '.join(char_fields)}",
            delete_after=5,
        )
    else:
        await ctx.send(
            f"Character attribute {attr} is ambiguous. Pick one of the following: {', '.join(char_fields)}",
            delete_after=5,
        )


@commands.command(usage="[character name]")
async def remove(ctx: Any, *args: str) -> None:
    """Removes a character from the bot.

    If the Discord user manages only a single character, the character name is optional and can be omitted.
    If the Discord user manages more than one character, the character name is required.

    The character name can be an abbreviation.
    For example, if the full name of a character is "Mediocre Mel", then typing "Med" is sufficient.
    That's as long as no other character name starts with "Med"."""
    cdi: CharacterData = ctx.bot.initbot_state.characters.get_from_tokens(
        args, ctx.author.name
    )
    ctx.bot.initbot_state.characters.remove_and_store(cdi)
    await ctx.send(f"Removed character {cdi.name}", delete_after=3)


@commands.command()
async def chars(ctx: Any) -> None:
    """Displays all characters known to the bot."""
    parts = (
        f"- {idx}: **{cdi.name}** (_{cdi.user}_)\n"
        for idx, cdi in enumerate(ctx.bot.initbot_state.characters.get_all())
    )
    await send_in_parts(ctx, parts)


@commands.command()
async def char(ctx: Any, *args: str) -> None:
    """Displays a character.

    If the Discord user manages only a single character, the character name is optional and can be omitted.
    If the Discord user manages more than one character, the character name is required.

    The character name can be an abbreviation.
    For example, if the full name of a character is "Mediocre Mel", then typing "Med" is sufficient.
    That's as long as no other character name starts with "Med"."""
    cdi: CharacterData = ctx.bot.initbot_state.characters.get_from_tokens(
        args, ctx.author.name
    )
    await ctx.send(str(cdi))


@commands.command()
async def park(ctx: Any, *args: str) -> None:
    """Deactivates a character so it is no longer included in the initiative order.

    If the Discord user manages only a single character, the character name is optional and can be omitted.
    If the Discord user manages more than one character, the character name is required.

    The character name can be an abbreviation.
    For example, if the full name of a character is "Mediocre Mel", then typing "Med" is sufficient.
    That's as long as no other character name starts with "Med"."""
    cdi: CharacterData = ctx.bot.initbot_state.characters.get_from_tokens(
        args, ctx.author.name
    )
    cdi.active = False
    ctx.bot.initbot_state.characters.update_and_store(cdi)
    await ctx.send(f"{cdi.name} is now inactive", delete_after=3)


@commands.command()
async def play(ctx: Any, *args: str) -> None:
    """Activates a character deactivated with the 'park' command so it is included in the initiative order again.

    If the Discord user manages only a single character, the character name is optional and can be omitted.
    If the Discord user manages more than one character, the character name is required.

    The character name can be an abbreviation.
    For example, if the full name of a character is "Mediocre Mel", then typing "Med" is sufficient.
    That's as long as no other character name starts with "Med"."""
    cdi: CharacterData = ctx.bot.initbot_state.characters.get_from_tokens(
        args, ctx.author.name
    )
    cdi.active = True
    ctx.bot.initbot_state.characters.update_and_store(cdi)
    await ctx.send(f"{cdi.name} is now active", delete_after=3)


@commands.command(usage="[all_players]")
async def unused(ctx: Any, *args: str) -> None:
    """Lists characters that haven't been used in a while and might be worth removing.

    By default, this command only lists the requesting player's own characters.
    Pass 'all_players' to list eligible characters belonging to any player."""
    show_all = "all_players" in args
    threshold = CORE_CFG.prune_threshold_days
    eligible = [
        cdi
        for cdi in ctx.bot.initbot_state.characters.get_all()
        if is_eligible_for_pruning(cdi, threshold)
        and (show_all or cdi.user == ctx.author.name)
    ]
    if not eligible:
        await ctx.send("You don't seem to have any unused characters.", delete_after=5)
        return
    parts = (f"- **{cdi.name}** (_{cdi.user}_)\n" for cdi in eligible)
    await send_in_parts(ctx, parts)


@commands.command(usage="[all_players]")
async def prune(ctx: Any, *args: str) -> None:
    """Removes all characters that haven't been used in a while.

    By default, only prunes the requesting player's own characters.
    Pass 'all_players' to prune unused characters belonging to any player.
    Replies with the names of the pruned characters."""
    show_all = "all_players" in args
    threshold = CORE_CFG.prune_threshold_days
    to_prune = [
        cdi
        for cdi in ctx.bot.initbot_state.characters.get_all()
        if is_eligible_for_pruning(cdi, threshold)
        and (show_all or cdi.user == ctx.author.name)
    ]
    for cdi in to_prune:
        ctx.bot.initbot_state.characters.remove_and_store(cdi)
    if not to_prune:
        await ctx.send("No characters to prune.", delete_after=5)
        return
    await ctx.send("Pruned: " + ", ".join(cdi.name for cdi in to_prune))


@commands.command(usage="[character name] [character name ...]")
async def touch(ctx: Any, *args: str) -> None:
    """Marks one or more characters as recently used, so they are not considered for pruning.

    Each argument is treated as a separate character name or abbreviation.
    If the Discord user manages only a single character, the character name is optional.

    The character name can be an abbreviation.
    For example, if the full name of a character is "Mediocre Mel", then typing "Med" is sufficient.
    That's as long as no other character name starts with "Med"."""
    tokens: tuple = args if args else ((),)
    touched = []
    for token in tokens:
        name_arg = (token,) if token else ()
        cdi: CharacterData = ctx.bot.initbot_state.characters.get_from_tokens(
            name_arg, ctx.author.name
        )
        ctx.bot.initbot_state.characters.update_and_store(cdi)
        touched.append(cdi.name)
    await ctx.send(
        "Marked as recently used: " + ", ".join(touched),
        delete_after=3,
    )


@new.error
@set_.error
@remove.error
@chars.error
@char.error
@park.error
@play.error
@unused.error
@prune.error
@touch.error
async def char_error(ctx, error):
    logging.exception(ctx.command)
    await ctx.send(str(error), delete_after=5)
