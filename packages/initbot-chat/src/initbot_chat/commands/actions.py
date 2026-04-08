# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
from typing import Final

from discord.ext import commands

from initbot_chat.commands.utils import send_in_parts, sync_player
from initbot_core.models.roll import contains_dice_rolls, render_dice_rolls_in_text

_SUBCOMMANDS: Final = frozenset({"list", "add", "update", "remove"})


def _split_actions_args(
    args: tuple[str, ...],
) -> tuple[list[str], str, list[str]]:
    """Split args into (name_tokens, subcommand, sub_args).

    Scans left-to-right for the first token matching a subcommand keyword.
    Raises ValueError if no subcommand keyword is found.
    """
    for i, token in enumerate(args):
        if token.lower() in _SUBCOMMANDS:
            return list(args[:i]), token.lower(), list(args[i + 1 :])
    raise ValueError(
        "Usage: `$actions [character] list|add|update|remove [args]`\n"
        "Example: `$actions add Mel attacks at d20+3 for 2d6 damage`"
    )


async def _list_actions(ctx: commands.Context, char_name: str) -> None:
    templates = ctx.bot.initbot_state.character_actions.get_all_for_character(char_name)
    if not templates:
        await ctx.send(f"{char_name} has no actions.", delete_after=5)
        return
    await send_in_parts(
        ctx,
        (
            f"{char_name} knows these actions:",
            *(f"{i}. {t}" for i, t in enumerate(templates, start=1)),
        ),
    )


@commands.command(
    name="actions", usage="[character name] list|add|update|remove [args]"
)
async def actions_cmd(ctx: commands.Context, *args: str) -> None:
    """Manage character actions.

    Character actions are shortcuts for common dice rolls of a character.
    For example, your character may have two preferred attacks and you find yourself typing "Mediocre Mel attacks with an axe at d20+5 for d12+3 damage" and "Mediocre Mel attacks with a Javelin at d20+3 for d8+1 damage" again and again.
    Actions bring this down to `$act 1` and `$act 2` and the chat bot replies with the same responses as above, including resolving the dice rolls.
    You just store those actions as templates ahead of time and can then use them by their action numbers.

    Subcommands:
    - list — show the actions that a character knows (including their action numbers).
    - add TEMPLATE — add a new action template containing at least one dice roll
    - update NR TEMPLATE — change the template of the action with the given action number.
    - remove NR — delete the action with the given action number.

    You can specify a character name or omit it.
    If you manage only a single character, omit it: `$actions list`
    If you manage more than one character or want to manage the actions of someone else's character, include the name: `$actions Mediocre Mel list`

    The character name can be an abbreviation.
    For example, if the full name of a character is "Mediocre Mel", then typing "med" is sufficient: `$actions med list`
    """
    player = sync_player(ctx.bot.initbot_state, ctx)
    state = ctx.bot.initbot_state
    name_tokens, subcommand, sub_args = _split_actions_args(args)
    cdi = state.characters.get_from_tokens(
        name_tokens, ctx.author.name, player_id=player.id
    )
    char_actions = state.character_actions

    if subcommand == "list":
        await _list_actions(ctx, cdi.name)

    elif subcommand == "add":
        if not sub_args:
            raise ValueError(
                "Provide a template after `add`, e.g. `$actions add attacks at d20+3`"
            )
        template = " ".join(sub_args)
        if not contains_dice_rolls(template):
            raise ValueError(
                f"Template must contain at least one dice roll (e.g. d20, 2d6+3). Got: '{template}'"
            )
        index = char_actions.add(cdi.name, template)
        await ctx.send(f"Added action #{index} for {cdi.name}.", delete_after=5)

    elif subcommand == "update":
        if len(sub_args) < 2 or not sub_args[0].isdigit():
            raise ValueError("Usage: `$actions [character] update IDX TEMPLATE`")
        template = " ".join(sub_args[1:])
        if not contains_dice_rolls(template):
            raise ValueError(
                f"Template must contain at least one dice roll (e.g. d20, 2d6+3). Got: '{template}'"
            )
        char_actions.update(cdi.name, int(sub_args[0]), template)
        await ctx.send(f"Updated action #{sub_args[0]} for {cdi.name}.", delete_after=5)

    elif subcommand == "remove":
        if not sub_args or not sub_args[0].isdigit():
            raise ValueError("Usage: `$actions [character] remove IDX`")
        idx = int(sub_args[0])
        templates = char_actions.get_all_for_character(cdi.name)
        if not 1 <= idx <= len(templates):
            count = len(templates)
            noun = "action" if count == 1 else "actions"
            await ctx.send(
                f"{cdi.name} only has {count} {noun}. Use `$actions list` to see them.",
                delete_after=10,
            )
            return
        char_actions.remove(cdi.name, idx)
        await ctx.send(
            f"Removed {cdi.name}'s action #{sub_args[0]} ({templates[idx - 1]})",
            delete_after=5,
        )


@commands.command(name="act", usage="[character name] NR")
async def act_cmd(ctx: commands.Context, *args: str) -> None:
    """Run an action of your or any other character.

    `$help actions` will get you started with character actions.

    For this $act command, you always need to provide the action number of the action you want to run.
    `$act` without an action number or `$actions list` tell you which actions a character knows and what their action numbers are.

    You can specify a character name or omit it.
    If you manage only a single character, omit it: `$act 1`
    If you manage more than one character or want to run an action of someone else's character, include the name: `$act Mediocre Mel 1`

    The character name can be an abbreviation.
    For example, if the full name of a character is "Mediocre Mel", then typing "med" is sufficient: `$act med 1`
    """
    player = sync_player(ctx.bot.initbot_state, ctx)
    state = ctx.bot.initbot_state

    if not args or not args[-1].isdigit():
        cdi = state.characters.get_from_tokens(
            list(args), ctx.author.name, player_id=player.id
        )
        await _list_actions(ctx, cdi.name)
        return

    index = int(args[-1])
    cdi = state.characters.get_from_tokens(
        list(args[:-1]), ctx.author.name, player_id=player.id
    )

    templates = state.character_actions.get_all_for_character(cdi.name)
    if not 1 <= index <= len(templates):
        raise ValueError(
            f"{cdi.name} has {len(templates)} action(s); index {index} is out of range."
        )

    await ctx.send(render_dice_rolls_in_text(templates[index - 1]))


@actions_cmd.error
@act_cmd.error
async def actions_error(ctx: commands.Context, error: commands.CommandError) -> None:
    logging.exception(ctx.command)
    await ctx.send(str(error), delete_after=5)
