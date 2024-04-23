# Copyright 2025 Stefan Götz <github.nooneelse@spamgourmet.com>

# This file is part of initbot.

# initbot is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.

# initbot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU Affero General Public
# License along with initbot. If not, see <https://www.gnu.org/licenses/>.


import re
import unittest

from initbot.models.roll import render_dice_rolls


class TestModelsRolls(unittest.TestCase):
    def test_render_dice_rolls(self):
        s = "d20+5 to attack the construct for 1d6+3 damage"
        result = render_dice_rolls(s.split())
        print(result)
        assert re.match(r"^(\d+) to attack the construct for (\d+) damage$", result)
