# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from collections.abc import Set
from typing import Any

from initbot_chat.commands.ability import abl, abls, mod, mods
from initbot_chat.commands.augur import augur, augurs
from initbot_chat.commands.character import (
    char,
    chars,
    new,
    park,
    play,
    prune,
    remove,
    set_,
    touch,
    unused,
)
from initbot_chat.commands.cls import classes, cls
from initbot_chat.commands.crit import crit
from initbot_chat.commands.init import inis, init
from initbot_chat.commands.levels import levels
from initbot_chat.commands.luck import luck
from initbot_chat.commands.occupation import occupations
from initbot_chat.commands.roll import roll
from initbot_chat.commands.tarot import tarot

commands: Set[Any] = frozenset((
    abl,
    abls,
    augur,
    augurs,
    char,
    chars,
    classes,
    cls,
    crit,
    inis,
    init,
    levels,
    luck,
    mod,
    mods,
    new,
    occupations,
    park,
    play,
    prune,
    remove,
    roll,
    set_,
    touch,
    unused,
    tarot,
))
