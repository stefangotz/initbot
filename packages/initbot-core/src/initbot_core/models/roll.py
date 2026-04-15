# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import random
import re
from abc import ABC, abstractmethod
from collections.abc import Iterable, Set
from dataclasses import dataclass
from typing import Final

_CRITICAL_FAILURE_EMOJIS: Final = ("😭", "😱", "💩", "🚽", "💔")

_DIE_TERM_PATTERN: Final = re.compile(r"^([0-9]*)d([0-9]+)$", re.IGNORECASE)
_REPEAT_PREFIX_PATTERN: Final = re.compile(r"^([0-9]+)x(.+)$", re.IGNORECASE)

# Characters stripped from word boundaries when scanning prose for dice specs.
# Parentheses are intentionally excluded: they are part of the Nx(expr) syntax
# and must not be stripped before the spec reaches DiceExpression.create().
_PROSE_STRIP_CHARS: Final = ".,!?;:[]{}\"'-"


def render_dice_rolls(words: Iterable[str]) -> str:
    return " ".join(map(_try_to_render_dice_roll, words))


def _try_to_detect_and_render_dice_roll(
    word: str, context: str = ""
) -> tuple[str, bool]:
    """Attempts to render a dice roll, returns (result, was_dice_roll)."""
    if any(
        phrase in context.lower()
        for phrase in ["system", "edition", "game", "rulebook"]
    ):
        return word, False

    for cls in _DICE_ROLL_CLASSES:
        try:
            return cls.create(word).roll(), True
        except ValueError:
            continue
    return word, False


def render_dice_rolls_in_text(text: str) -> str:
    """Replaces dice roll expressions found in text with their rolled results."""
    words = text.split()
    result_words = []

    for word in words:
        clean_word = word.strip(_PROSE_STRIP_CHARS)
        rendered_word, was_dice = _try_to_detect_and_render_dice_roll(clean_word, text)

        if was_dice:
            prefix = word[: len(word) - len(word.lstrip(_PROSE_STRIP_CHARS))]
            suffix = word[len(word.rstrip(_PROSE_STRIP_CHARS)) :]
            result_words.append(prefix + rendered_word + suffix)
        else:
            result_words.append(word)

    return " ".join(result_words)


def contains_dice_rolls(text: str) -> bool:
    words = text.split()
    for word in words:
        clean_word = word.strip(_PROSE_STRIP_CHARS)
        _, was_dice = _try_to_detect_and_render_dice_roll(clean_word, text)
        if was_dice:
            return True
    return False


def _try_to_render_dice_roll(word: str) -> str:
    for cls in _DICE_ROLL_CLASSES:
        try:
            return cls.create(word).roll()
        except ValueError:
            continue
    return word


class _DiceRoll(ABC):
    @abstractmethod
    def roll(self) -> str:
        pass

    @classmethod
    def is_valid_spec(cls, spec: str) -> bool:
        try:
            return cls.create(spec) is not None
        except ValueError:
            return False

    @staticmethod
    @abstractmethod
    def create(spec: str) -> "_DiceRoll":
        pass


@dataclass(frozen=True)
class _DieTerm:
    sides: int
    count: int = 1

    def roll(self) -> int:
        return sum(random.randint(1, self.sides) for _ in range(self.count))

    @property
    def min_value(self) -> int:
        return self.count

    @property
    def max_value(self) -> int:
        return self.count * self.sides


def _parse_die_term(token: str) -> _DieTerm:
    """Parse a token like 'd6', '2d6', 'd20' into a _DieTerm. Raises ValueError on failure."""
    match = _DIE_TERM_PATTERN.match(token)
    if not match:
        raise ValueError(f"'{token}' is not a valid die term")
    count = int(match.group(1)) if match.group(1) else 1
    sides = int(match.group(2))
    return _DieTerm(sides=sides, count=count)


def _tokenise(expr: str) -> list[tuple[int, str]]:
    """Split a dice expression into signed tokens.

    Returns a list of (sign, token) pairs where sign is +1 or -1.
    Example: 'd20+d8-3' → [(+1,'d20'), (+1,'d8'), (-1,'3')]
    """
    tokens: list[tuple[int, str]] = []
    current = ""
    sign = 1
    for ch in expr:
        if ch in ("+", "-") and current:
            tokens.append((sign, current))
            current = ""
            sign = 1 if ch == "+" else -1
        else:
            current += ch
    if current:
        tokens.append((sign, current))
    return tokens


@dataclass(frozen=True)
class DiceExpression(_DiceRoll):
    """A dice expression with one or more signed terms and an optional repeat count.

    Supports specs like: d6, 2d6, d20+5, d20+d8+d6, 2xd20, 2x(d20+d8-3).
    """

    terms: tuple[tuple[int, "_DieTerm | int"], ...]
    repeat: int = 1

    def roll_one(self) -> int:
        """Roll the expression once and return the integer total."""
        return sum(
            sign * (term.roll() if isinstance(term, _DieTerm) else term)
            for sign, term in self.terms
        )

    def _is_single_die(self) -> bool:
        """True when the expression has exactly one die term with count=1 (constants allowed)."""
        die_terms = [(s, t) for s, t in self.terms if isinstance(t, _DieTerm)]
        return len(die_terms) == 1 and die_terms[0][1].count == 1

    def _expression_min(self) -> int:
        return sum(
            s * (t.min_value if isinstance(t, _DieTerm) else t) for s, t in self.terms
        )

    def _expression_max(self) -> int:
        return sum(
            s * (t.max_value if isinstance(t, _DieTerm) else t) for s, t in self.terms
        )

    def _format_single(self, value: int) -> str:
        if self._is_single_die():
            if value == self._expression_min():
                return f"**{value}** {random.choice(_CRITICAL_FAILURE_EMOJIS)}"
            if value == self._expression_max():
                return f"**{value}** \U0001f3af"
        return str(value)

    def roll(self) -> str:
        if self.repeat == 1:
            return self._format_single(self.roll_one())
        raw = [self.roll_one() for _ in range(self.repeat)]
        parts = [self._format_single(v) for v in raw]
        return "+".join(parts) + f"={sum(raw)}"

    def __str__(self) -> str:
        parts = []
        for i, (sign, term) in enumerate(self.terms):
            prefix = ("" if sign == 1 else "-") if i == 0 else "+" if sign == 1 else "-"
            if isinstance(term, _DieTerm):
                die_str = (
                    f"{term.count}d{term.sides}"
                    if term.count != 1
                    else f"d{term.sides}"
                )
                parts.append(prefix + die_str)
            else:
                parts.append(prefix + str(term))
        expr = "".join(parts)
        if self.repeat == 1:
            return expr
        needs_parens = len(self.terms) > 1 or (
            len(self.terms) == 1 and isinstance(self.terms[0][1], int)
        )
        inner = f"({expr})" if needs_parens else expr
        return f"{self.repeat}x{inner}"

    @staticmethod
    def create(spec: str) -> "DiceExpression":
        """Parse a dice spec string into a DiceExpression. Raises ValueError on failure."""
        repeat = 1
        remainder = spec

        repeat_match = _REPEAT_PREFIX_PATTERN.match(spec)
        if repeat_match:
            repeat = int(repeat_match.group(1))
            remainder = repeat_match.group(2)

        if remainder.startswith("("):
            remainder = remainder[1:]
            if remainder.endswith(")"):
                remainder = remainder[:-1]

        raw_tokens = _tokenise(remainder)
        if not raw_tokens:
            raise ValueError(f"'{spec}' is not a valid dice expression")

        terms: list[tuple[int, _DieTerm | int]] = []
        has_die = False
        for sign, token in raw_tokens:
            try:
                die = _parse_die_term(token)
                terms.append((sign, die))
                has_die = True
            except ValueError:
                try:
                    terms.append((sign, int(token)))
                except ValueError as exc:
                    raise ValueError(
                        f"'{token}' in '{spec}' is not a valid die term or integer"
                    ) from exc

        if not has_die:
            raise ValueError(
                f"'{spec}' contains no dice — use a die spec like d6 or 2d20"
            )

        return DiceExpression(terms=tuple(terms), repeat=repeat)


_DICE_ROLL_CLASSES: Set[type[_DiceRoll]] = frozenset((DiceExpression,))
