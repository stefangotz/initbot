# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later


import re
import unittest
from unittest.mock import patch

import pytest

from initbot_core.models.roll import (
    DiceExpression,
    render_dice_rolls,
    render_dice_rolls_in_text,
)


class TestRenderDiceRolls(unittest.TestCase):
    def test_render_dice_rolls(self):
        s = "d20+5 to attack the construct for 1d6+3 damage"
        result = render_dice_rolls(s.split())
        # Result may contain bold/emoji for natural min/max, so allow optional formatting
        assert re.match(
            r"^(\*\*\d+\*\* .|\d+) to attack the construct for (\*\*\d+\*\* .|\d+) damage$",
            result,
        )

    def test_render_dice_rolls_in_text_repeat_compound_no_trailing_paren(self):
        # "1x(d20)" in plain chat must not produce a trailing ) in the output.
        # repeat=1 rolls once and returns a plain number (no v1+...=total format).
        result = render_dice_rolls_in_text("roll 1x(d20) for initiative")
        assert ")" not in result
        assert re.search(r"roll (\*\*\d+\*\* .|\d+) for initiative", result)


class TestDiceExpressionHighlighting(unittest.TestCase):
    def test_single_die_natural_min(self):
        expr = DiceExpression.create("d6")
        with patch("random.randint", return_value=1):
            result = expr.roll()
            assert re.match(r"^\*\*1\*\* .$", result)

    def test_single_die_natural_max(self):
        expr = DiceExpression.create("d6")
        with patch("random.randint", return_value=6):
            assert expr.roll() == "**6** \U0001f3af"

    def test_single_die_ordinary(self):
        expr = DiceExpression.create("d6")
        with patch("random.randint", return_value=3):
            assert expr.roll() == "3"

    def test_single_die_with_modifier_natural_min(self):
        expr = DiceExpression.create("d20+5")
        with patch("random.randint", return_value=1):
            result = expr.roll()
            assert re.match(r"^\*\*6\*\* .$", result)

    def test_single_die_with_modifier_natural_max(self):
        expr = DiceExpression.create("d20+5")
        with patch("random.randint", return_value=20):
            assert expr.roll() == "**25** \U0001f3af"

    def test_multiple_dice_no_highlight(self):
        expr = DiceExpression.create("2d6")
        with patch("random.randint", return_value=1):
            assert expr.roll() == "2"

    def test_compound_no_highlight(self):
        expr = DiceExpression.create("d20+d8")
        with patch("random.randint", return_value=1):
            assert expr.roll() == "2"
            assert "**" not in expr.roll()

    def test_multi_roll_single_die_highlights_individuals(self):
        expr = DiceExpression.create("3xd6")
        with patch("random.randint", side_effect=[1, 6, 3]):
            result = expr.roll()
        assert re.search(r"\*\*1\*\* .", result)
        assert "**6** \U0001f3af" in result
        assert result.endswith("=10")

    def test_multi_roll_multiple_dice_no_highlight(self):
        expr = DiceExpression.create("3x2d6")
        with patch("random.randint", return_value=1):
            result = expr.roll()
        assert "**" not in result


class TestDiceExpressionCompound(unittest.TestCase):
    def test_two_die_terms(self):
        expr = DiceExpression.create("d20+d8")
        value = expr.roll_one()
        assert isinstance(value, int)
        assert 2 <= value <= 28

    def test_three_die_terms(self):
        expr = DiceExpression.create("d20+d8+d6")
        value = expr.roll_one()
        assert isinstance(value, int)
        assert 3 <= value <= 44

    def test_mixed_dice_and_constant(self):
        expr = DiceExpression.create("2d6+d4+3")
        value = expr.roll_one()
        assert isinstance(value, int)
        assert 6 <= value <= 18

    def test_subtraction(self):
        expr = DiceExpression.create("d20-d6")
        value = expr.roll_one()
        assert isinstance(value, int)
        assert -5 <= value <= 19

    def test_roll_one_returns_int(self):
        expr = DiceExpression.create("d20+d8+3")
        result = expr.roll_one()
        assert isinstance(result, int)

    def test_single_roll_no_equals(self):
        expr = DiceExpression.create("d20+d8")
        result = expr.roll()
        assert "=" not in result


class TestDiceExpressionRepeat(unittest.TestCase):
    def test_two_x_single_die_format(self):
        expr = DiceExpression.create("2xd20")
        result = expr.roll()
        assert re.match(r"^(\*\*\d+\*\* .|\d+)\+(\*\*\d+\*\* .|\d+)=\d+$", result)

    def test_two_x_compound_format(self):
        expr = DiceExpression.create("2x(d20-d3+5)")
        result = expr.roll()
        assert re.match(r"^\d+\+\d+=\d+$", result)

    def test_three_x_mocked_values(self):
        expr = DiceExpression.create("3xd6")
        with patch("random.randint", side_effect=[1, 6, 3]):
            result = expr.roll()
        assert re.search(r"\*\*1\*\* .", result)
        assert "**6** \U0001f3af" in result
        assert result.endswith("=10")

    def test_repeat_total_is_correct(self):
        expr = DiceExpression.create("2xd6")
        with patch("random.randint", side_effect=[4, 3]):
            result = expr.roll()
        assert result == "4+3=7"

    def test_repeat_compound_total_is_correct(self):
        expr = DiceExpression.create("2x(d6+d4)")
        with patch("random.randint", side_effect=[5, 3, 2, 4]):
            result = expr.roll()
        assert result == "8+6=14"

    def test_repeat_with_unmatched_open_paren(self):
        # create() tolerates a leading ( without a matching ) e.g. from callers
        # that strip trailing punctuation before parsing
        expr = DiceExpression.create("2x(d6")
        with patch("random.randint", side_effect=[5, 2]):
            result = expr.roll()
        assert result == "5+2=7"


class TestDiceExpressionCreate(unittest.TestCase):
    def test_invalid_spec_raises(self):
        with pytest.raises(ValueError, match="notadice"):
            DiceExpression.create("notadice")

    def test_plain_integer_raises(self):
        with pytest.raises(ValueError, match="no dice"):
            DiceExpression.create("5")

    def test_is_valid_spec_true(self):
        assert DiceExpression.is_valid_spec("d20+d8")

    def test_is_valid_spec_false(self):
        assert not DiceExpression.is_valid_spec("hello")
