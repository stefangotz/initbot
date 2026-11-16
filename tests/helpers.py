# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import pathlib
from collections.abc import Awaitable, Callable
from typing import Any, cast

from discord.ext import commands

DATA_DIR = pathlib.Path(__file__).parent / "data"
REFERENCE_FILES: list[str] = []


async def _invoke_command(
    command: commands.Command[Any, ..., Any], ctx: Any, *args: str
) -> Any:
    callback = cast(Callable[..., Awaitable[Any]], command.callback)
    return await callback(ctx, *args)


async def _invoke_handler(handler: object, *args: Any) -> Any:
    callback = cast(Callable[..., Awaitable[Any]], handler)
    return await callback(*args)


def predicate_from(check_decorator: Callable[..., Any]) -> Callable[..., Any]:
    async def _dummy(_ctx): ...

    check_decorator(_dummy)
    return vars(_dummy)["__commands_checks__"][0]
