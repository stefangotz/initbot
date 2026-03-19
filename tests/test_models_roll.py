# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later


import re
import unittest

from initbot_core.models.roll import render_dice_rolls


class TestModelsRolls(unittest.TestCase):
    def test_render_dice_rolls(self):
        s = "d20+5 to attack the construct for 1d6+3 damage"
        result = render_dice_rolls(s.split())
        print(result)
        assert re.match(r"^(\d+) to attack the construct for (\d+) damage$", result)
