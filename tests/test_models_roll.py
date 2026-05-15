# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later


import re
import unittest
from unittest.mock import patch

import pytest

from initbot_core.models.roll import (
    DiceExpression,
    KeepExpression,
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
        assert 3 <= value <= 34

    def test_mixed_dice_and_constant(self):
        expr = DiceExpression.create("2d6+d4+3")
        value = expr.roll_one()
        assert isinstance(value, int)
        assert 6 <= value <= 19

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


class TestKeepExpressionCreate(unittest.TestCase):
    def test_adv_basic(self):
        expr = KeepExpression.create("d20adv")
        assert expr.keep_highest is True
        assert expr.count == 2
        assert expr.keep == 1

    def test_dis_basic(self):
        expr = KeepExpression.create("d20dis")
        assert expr.keep_highest is False
        assert expr.count == 2
        assert expr.keep == 1

    def test_adv_with_modifier(self):
        expr = KeepExpression.create("d20+5adv")
        assert expr.keep_highest is True
        assert str(expr.base) == "d20+5"

    def test_adv_compound(self):
        expr = KeepExpression.create("d20+d8adv")
        assert expr.keep_highest is True
        assert str(expr.base) == "d20+d8"

    def test_kh_basic(self):
        expr = KeepExpression.create("2d20kh1")
        assert expr.count == 2
        assert expr.sides == 20
        assert expr.keep == 1
        assert expr.keep_highest is True

    def test_kl_multi_keep(self):
        expr = KeepExpression.create("3d6kl2")
        assert expr.count == 3
        assert expr.sides == 6
        assert expr.keep == 2
        assert expr.keep_highest is False

    def test_kh_no_leading_count_invalid(self):
        with pytest.raises(ValueError, match="d20kh1"):
            KeepExpression.create("d20kh1")

    def test_kh_count_one_invalid(self):
        with pytest.raises(ValueError, match="count >= 2"):
            KeepExpression.create("1d20kh1")

    def test_kh_keep_equals_count_invalid(self):
        with pytest.raises(ValueError, match="keep"):
            KeepExpression.create("2d20kh2")

    def test_kh_keep_zero_invalid(self):
        with pytest.raises(ValueError, match="keep"):
            KeepExpression.create("2d20kh0")

    def test_a_alias_for_adv(self):
        expr = KeepExpression.create("d20a")
        assert expr.keep_highest is True
        assert expr.count == 2

    def test_d_alias_for_dis(self):
        expr = KeepExpression.create("d20d")
        assert expr.keep_highest is False
        assert expr.count == 2

    def test_alias_canonicalises_to_long_form(self):
        assert str(KeepExpression.create("d20+5a")) == "d20+5adv"
        assert str(KeepExpression.create("d20d")) == "d20dis"

    def test_invalid_base_invalid(self):
        with pytest.raises(ValueError, match=r"namedis|name"):
            KeepExpression.create("namedis")

    def test_plain_dice_invalid(self):
        with pytest.raises(ValueError, match="d20"):
            KeepExpression.create("d20")


class TestKeepExpressionRollOne(unittest.TestCase):
    def test_kh_keeps_highest(self):
        expr = KeepExpression.create("2d20kh1")
        with patch("random.randint", side_effect=[8, 14]):
            assert expr.roll_one() == 14

    def test_kl_sums_lowest(self):
        expr = KeepExpression.create("3d6kl2")
        with patch("random.randint", side_effect=[4, 1, 6]):
            assert expr.roll_one() == 5  # 1 + 4

    def test_adv_keeps_highest(self):
        expr = KeepExpression.create("d20adv")
        with patch("random.randint", side_effect=[8, 14]):
            assert expr.roll_one() == 14

    def test_dis_keeps_lowest(self):
        expr = KeepExpression.create("d20dis")
        with patch("random.randint", side_effect=[19, 13]):
            assert expr.roll_one() == 13

    def test_roll_one_returns_int(self):
        expr = KeepExpression.create("d20adv")
        assert isinstance(expr.roll_one(), int)


class TestKeepExpressionRoll(unittest.TestCase):
    def test_adv_kept_shown_plain_dropped_struck(self):
        expr = KeepExpression.create("d20adv")
        with patch("random.randint", side_effect=[14, 8]):
            assert expr.roll() == "14 ~~8~~"

    def test_dis_dropped_shown_struck(self):
        expr = KeepExpression.create("d20dis")
        with patch("random.randint", side_effect=[19, 13]):
            assert expr.roll() == "~~19~~ 13"

    def test_kh_strikethrough_on_dropped(self):
        expr = KeepExpression.create("2d20kh1")
        with patch("random.randint", side_effect=[8, 14]):
            assert expr.roll() == "~~8~~ 14"

    def test_kh_natural_max_highlighted(self):
        expr = KeepExpression.create("2d20kh1")
        with patch("random.randint", side_effect=[1, 20]):
            result = expr.roll()
        assert "**20** \U0001f3af" in result
        assert "~~1~~" in result

    def test_kl_multi_keep_shows_sum(self):
        expr = KeepExpression.create("3d6kl2")
        with patch("random.randint", side_effect=[4, 1, 6]):
            result = expr.roll()
        # 1 is the natural min for d6, so it gets highlighted; 6 is dropped (struck through)
        assert re.search(r"\*\*1\*\* .", result)
        assert "~~6~~" in result
        assert result.endswith("=5")

    def test_adv_tie_keeps_first(self):
        expr = KeepExpression.create("d20adv")
        with patch("random.randint", side_effect=[15, 15]):
            assert expr.roll() == "15 ~~15~~"

    def test_adv_natural_max_highlighted(self):
        expr = KeepExpression.create("d20adv")
        with patch("random.randint", side_effect=[20, 8]):
            result = expr.roll()
        assert "**20** \U0001f3af" in result


class TestKeepExpressionStr(unittest.TestCase):
    def test_str_adv(self):
        assert str(KeepExpression.create("d20adv")) == "d20adv"

    def test_str_dis_with_modifier(self):
        assert str(KeepExpression.create("d20+5dis")) == "d20+5dis"

    def test_str_kh(self):
        assert str(KeepExpression.create("2d20kh1")) == "2d20kh1"

    def test_str_kl(self):
        assert str(KeepExpression.create("3d6kl2")) == "3d6kl2"


class TestKeepExpressionInText(unittest.TestCase):
    def test_render_adv_in_text(self):
        result = render_dice_rolls_in_text("roll d20adv for initiative")
        assert "d20adv" not in result
        assert re.search(r"roll .+ for initiative", result)

    def test_render_kh_in_text(self):
        result = render_dice_rolls_in_text("roll 2d20kh1 to attack")
        assert "2d20kh1" not in result
        assert re.search(r"roll .+ to attack", result)
