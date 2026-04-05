# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import pathlib
from collections.abc import Callable
from typing import Any

DATA_DIR = pathlib.Path(__file__).parent / "data"
REFERENCE_FILES: list[str] = []


def predicate_from(check_decorator: Callable[..., Any]) -> Callable[..., Any]:
    async def _dummy(_ctx): ...

    check_decorator(_dummy)
    return _dummy.__commands_checks__[0]  # type: ignore[unresolved-attribute]  # pylint: disable=no-member
