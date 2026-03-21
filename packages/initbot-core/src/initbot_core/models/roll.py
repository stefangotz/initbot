# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import random
import re
from abc import ABC, abstractmethod
from collections.abc import Iterable, Sequence, Set
from dataclasses import dataclass

_NERD_DICE_ROLL_PATTERN = re.compile(
    r"^(([0-9]+)x)?([0-9]*)d([0-9]+)([+-][0-9]+)?$", re.IGNORECASE
)


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
        clean_word = word.strip(".,!?;:()[]{}\"'-")
        rendered_word, was_dice = _try_to_detect_and_render_dice_roll(clean_word, text)

        if was_dice:
            prefix = word[: len(word) - len(word.lstrip(".,!?;:()[]{}\"'-"))]
            suffix = word[len(word.rstrip(".,!?;:()[]{}\"'-")) :]
            result_words.append(prefix + rendered_word + suffix)
        else:
            result_words.append(word)

    return " ".join(result_words)


def contains_dice_rolls(text: str) -> bool:
    words = text.split()
    for word in words:
        clean_word = word.strip(".,!?;:()[]{}\"'-")
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


class IntDiceRoll(_DiceRoll, ABC):
    def roll(self) -> str:
        rolls = self.roll_all()
        if len(rolls) == 1:
            return str(rolls[0])
        return f"{sum(rolls)} ({str(rolls).strip('[]')})"

    @abstractmethod
    def roll_all(self) -> Sequence[int]:
        pass

    @abstractmethod
    def roll_one(self) -> int:
        pass


@dataclass(frozen=True)
class NerdDiceRoll(IntDiceRoll):
    sides: int
    dice: int = 1
    modifier: int = 0
    rolls: int = 1

    def roll_all(self) -> Sequence[int]:
        return tuple(self.roll_one() for _ in range(0, self.rolls))

    def roll_one(self) -> int:
        return (
            sum(random.randint(1, self.sides) for _ in range(0, self.dice))
            + self.modifier
        )

    def __str__(self) -> str:
        result = ""
        if self.rolls != 1:
            result += f"{self.rolls}x"
        if self.dice != 1:
            result += str(self.dice)
        result += f"d{self.sides}"
        if self.modifier != 0:
            if self.modifier > 0:
                result += "+"
            result += str(self.modifier)
        return result

    def _format_die_value(self, value: int) -> str:
        if self.dice == 1:
            if value == self.dice + self.modifier:
                return f"**{value}** \U0001f480"
            if value == self.dice * self.sides + self.modifier:
                return f"**{value}** \U0001f3af"
        return str(value)

    def roll(self) -> str:
        rolls = self.roll_all()
        if self.rolls == 1:
            if self.dice == 1:
                return self._format_die_value(rolls[0])
            return (
                str(rolls[0])
                if len(rolls) == 1
                else f"{sum(rolls)} ({str(list(rolls)).strip('[]')})"
            )
        formatted = [self._format_die_value(r) for r in rolls]
        return f"{sum(rolls)} ({', '.join(formatted)})"

    @staticmethod
    def create(spec: str) -> "NerdDiceRoll":
        match = _NERD_DICE_ROLL_PATTERN.match(spec)
        if match:
            args = {"sides": int(match.group(4))}
            if match.group(3):
                args["dice"] = int(match.group(3))
            if match.group(5):
                args["modifier"] = int(match.group(5))
            if match.group(2):
                args["rolls"] = int(match.group(2))
            return NerdDiceRoll(**args)
        raise ValueError(f"'{spec}' is not supported")


_DICE_ROLL_CLASSES: Set[type[_DiceRoll]] = frozenset((NerdDiceRoll,))
