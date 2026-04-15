# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
from datetime import datetime

from discord import Embed
from discord.ext import commands

from initbot_chat.commands.character import CharacterData, characters
from initbot_chat.commands.utils import player_name, sync_player
from initbot_core.models.roll import DiceExpression
from initbot_core.utils import is_int


@commands.command(usage="[character name] initiative *or* initiative [character name]")
async def init(ctx: commands.Context, *args: str) -> None:
    """Sets the initiative of a character.

    This sets a character's initiative to the specified *initiative*, primarily so that the *inis* command ranks the character by its initiative.

    If the Discord user manages only a single character, the character name is optional and can be omitted: `$init 10`
    If the Discord user manages more than one character, the character name is required: `$init Mediocre Mel 10`

    The character name can be an abbreviation.
    For example, if the full name of a character is "Mediocre Mel", then typing "med" is sufficient: `$init med 10`
    That's as long as no other character name starts with "med".

    If there is no character with the given name, a new character with that name is created.

    The bot can roll initiative itself with this command.
    To make that work, set the character's initiative dice first with `$init_dice`.
    With that set up, make the bot automatically roll initiative simply by omitting the initiative value: `$init Mediocre Mel`

    Thus, in the shortest (and most common case), one can simply use the command `$init` by itself to automatically roll and set a character's initiative.
    """
    player = sync_player(ctx.bot.initbot_state, ctx)
    tokens = list(args)
    if len(tokens) > 4:
        raise ValueError("Too long")
    if len(tokens) == 0:
        initiative = None
        name = []
    elif is_int(tokens[-1]):
        initiative = int(tokens[-1])
        name = tokens[0:-1]
    elif is_int(tokens[0]):
        initiative = int(tokens[0])
        name = tokens[1:]
    else:
        initiative = None
        name = tokens
    cdi: CharacterData = ctx.bot.initbot_state.characters.get_from_tokens(
        name, create=len(name) > 0, player_id=player.id
    )
    if initiative is None:
        if cdi.initiative_dice is not None:
            initiative = DiceExpression.create(cdi.initiative_dice).roll_one()
        else:
            raise ValueError(
                f"No initiative dice set for {cdi.name}. Use `$init_dice {cdi.name} d20+3` first."
            )

    cdi.initiative = initiative
    cdi.last_used = int(datetime.now().timestamp())
    ctx.bot.initbot_state.characters.update_and_store(cdi)

    await ctx.send(f"{cdi.name}'s initiative is now {cdi.initiative}", delete_after=3)


@commands.command()
async def inis(ctx: commands.Context) -> None:
    """Lists characters in initiative order.

    Use the *init* command to set the initiative value of a character.
    Use the *remove* command to remove a character.

    Only characters whose initiative was set within the last 24 hours are shown.
    """

    def has_recent_initiative(cdi: CharacterData) -> bool:
        return (
            cdi.initiative is not None
            and cdi.last_used is not None
            and cdi.last_used > int(datetime.now().timestamp()) - 24 * 3600
        )

    sync_player(ctx.bot.initbot_state, ctx)
    state = ctx.bot.initbot_state
    sorted_characters = sorted(
        filter(has_recent_initiative, characters(state)),
        key=lambda c: c.initiative or 0,
        reverse=True,
    )
    desc: str = "\n".join(
        f"{cdi.initiative}: **{cdi.name}** (*{player_name(state, cdi)}*)"
        for cdi in sorted_characters
    )
    embed = Embed(title="Initiative Order", description=desc)
    await ctx.send(embed=embed)


@inis.error  # type: ignore  # stacking .error across cog/non-cog commands; valid at runtime
@init.error
async def init_error(ctx: commands.Context, error: commands.CommandError) -> None:
    logging.exception(ctx.command)
    await ctx.send(str(error), delete_after=5)
