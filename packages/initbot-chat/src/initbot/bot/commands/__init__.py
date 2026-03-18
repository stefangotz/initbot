# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from collections.abc import Set
from typing import Any

from initbot.bot.commands.ability import abl, abls, mod, mods
from initbot.bot.commands.augur import augur, augurs
from initbot.bot.commands.character import char, chars, new, park, play, remove, set_
from initbot.bot.commands.cls import classes, cls
from initbot.bot.commands.crit import crit
from initbot.bot.commands.init import inis, init
from initbot.bot.commands.levels import levels
from initbot.bot.commands.luck import luck
from initbot.bot.commands.occupation import occupations
from initbot.bot.commands.roll import roll
from initbot.bot.commands.tarot import tarot

commands: Set[Any] = frozenset(
    (
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
        remove,
        roll,
        set_,
        tarot,
    )
)
