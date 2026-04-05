# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from collections.abc import Set
from typing import Any

from initbot_chat.commands.character import (
    char,
    chars,
    init_dice,
    prune,
    remove,
    touch,
    unused,
)
from initbot_chat.commands.init import inis, init
from initbot_chat.commands.roll import roll
from initbot_chat.commands.tarot import tarot
from initbot_chat.commands.web import web

commands: Set[Any] = frozenset((
    char,
    chars,
    inis,
    init,
    init_dice,
    prune,
    remove,
    roll,
    touch,
    tarot,
    unused,
    web,
))
