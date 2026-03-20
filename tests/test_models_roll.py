# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later


import re
import unittest
from unittest.mock import patch

from initbot_core.models.roll import NerdDiceRoll, render_dice_rolls


class TestModelsRolls(unittest.TestCase):
    def test_render_dice_rolls(self):
        s = "d20+5 to attack the construct for 1d6+3 damage"
        result = render_dice_rolls(s.split())
        print(result)
        # Result may contain bold/emoji for natural min/max, so allow optional formatting
        assert re.match(
            r"^(\*\*\d+\*\* .|\d+) to attack the construct for (\*\*\d+\*\* .|\d+) damage$",
            result,
        )


class TestNerdDiceRollHighlighting(unittest.TestCase):
    def test_single_die_natural_min(self):
        roll = NerdDiceRoll(sides=6)
        with patch("random.randint", return_value=1):
            assert roll.roll() == "**1** \U0001f480"

    def test_single_die_natural_max(self):
        roll = NerdDiceRoll(sides=6)
        with patch("random.randint", return_value=6):
            assert roll.roll() == "**6** \U0001f3af"

    def test_single_die_ordinary(self):
        roll = NerdDiceRoll(sides=6)
        with patch("random.randint", return_value=3):
            assert roll.roll() == "3"

    def test_single_die_with_modifier_natural_min(self):
        roll = NerdDiceRoll(sides=20, modifier=5)
        with patch("random.randint", return_value=1):
            assert roll.roll() == "**6** \U0001f480"

    def test_single_die_with_modifier_natural_max(self):
        roll = NerdDiceRoll(sides=20, modifier=5)
        with patch("random.randint", return_value=20):
            assert roll.roll() == "**25** \U0001f3af"

    def test_multiple_dice_no_highlight(self):
        roll = NerdDiceRoll(sides=6, dice=2)
        with patch("random.randint", return_value=1):
            # All ones — but not highlighted for multi-die rolls
            assert roll.roll() == "2"

    def test_multiple_dice_no_highlight_with_breakdown(self):
        roll = NerdDiceRoll(sides=6, dice=2, rolls=1)
        # Both dice return 1 — no highlighting expected
        with patch("random.randint", return_value=1):
            result = roll.roll()
            assert "**" not in result
            assert "\U0001f480" not in result

    def test_multi_roll_single_die_highlights_individuals(self):
        roll = NerdDiceRoll(sides=6, rolls=3)
        # Returns 1, 6, 3 in sequence
        with patch("random.randint", side_effect=[1, 6, 3]):
            result = roll.roll()
        assert "**1** \U0001f480" in result
        assert "**6** \U0001f3af" in result
        assert result.startswith("10 (")

    def test_multi_roll_multiple_dice_no_highlight(self):
        roll = NerdDiceRoll(sides=6, dice=2, rolls=3)
        with patch("random.randint", return_value=1):
            result = roll.roll()
        assert "**" not in result
        assert "\U0001f480" not in result
