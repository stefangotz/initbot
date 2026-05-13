# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Structural HTML validation for server-rendered cell fragments.

These tests parse the HTML output of each inline-cell render function and verify
that all Datastar reactive attributes are present and contain the expected JS
fragments.  An f-string quoting error (e.g. an unescaped single quote inside a
double-quoted HTML attribute) would truncate the attribute value, causing these
checks to fail even when the template renders without a Python exception.
"""

import time
from html.parser import HTMLParser

from initbot_core.data.character import CharacterData
from initbot_core.data.player import PlayerData
from initbot_web.routes.tracker import (
    _render_combined_rows,
    _render_inline_dice_cell,
    _render_inline_init_cell,
    _render_inline_name_cell,
    _render_inline_player_cell,
)


class _AttributeCollector(HTMLParser):
    """Collect all (tag, attrs-dict) pairs from a parsed HTML fragment."""

    def __init__(self) -> None:
        super().__init__()
        self.elements: list[tuple[str, dict[str, str | None]]] = []
        self.parse_errors: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.elements.append((tag, dict(attrs)))

    def handle_error(self, message: str) -> None:  # type: ignore[override]
        self.parse_errors.append(message)


def _collect(fragment: str) -> list[tuple[str, dict[str, str | None]]]:
    p = _AttributeCollector()
    p.feed(fragment)
    assert not p.parse_errors, f"HTML parse errors: {p.parse_errors}"
    return p.elements


def test_inline_name_cell_attributes_are_well_formed() -> None:
    fragment = _render_inline_name_cell("Brother Thog", "/add")
    elems = _collect(fragment)
    inputs = [attrs for tag, attrs in elems if tag == "input"]
    assert len(inputs) == 1
    inp = inputs[0]
    kd = inp.get("data-on:keydown") or ""
    blur = inp.get("data-on:blur") or ""
    effect = inp.get("data-effect") or ""
    assert kd, "data-on:keydown missing or empty"
    assert blur, "data-on:blur missing or empty"
    assert effect, "data-effect missing or empty"
    assert "Escape" in kd
    assert "Tab" in kd
    assert "Enter" in kd
    assert "@post" in kd


def test_inline_init_cell_attributes_are_well_formed() -> None:
    fragment = _render_inline_init_cell("12", "/add")
    elems = _collect(fragment)
    inputs = [attrs for tag, attrs in elems if tag == "input"]
    assert len(inputs) == 1
    kd = inputs[0].get("data-on:keydown") or ""
    assert "Escape" in kd
    assert "Tab" in kd
    assert "@post" in kd


def test_inline_dice_cell_attributes_are_well_formed() -> None:
    fragment = _render_inline_dice_cell("d20+3", "/add")
    elems = _collect(fragment)
    inputs = [attrs for tag, attrs in elems if tag == "input"]
    assert len(inputs) == 1
    kd = inputs[0].get("data-on:keydown") or ""
    assert "Escape" in kd
    assert "Tab" in kd
    assert "@post" in kd


def test_inline_player_cell_attributes_are_well_formed() -> None:
    players = [
        PlayerData(id=1, discord_id=10, name="Alice"),
        PlayerData(id=2, discord_id=20, name="Bob"),
    ]
    fragment = _render_inline_player_cell("Alice", players, "/add")
    elems = _collect(fragment)
    selects = [attrs for tag, attrs in elems if tag == "select"]
    assert len(selects) == 1
    sel = selects[0]
    kd = sel.get("data-on:keydown") or ""
    assert sel.get("data-on:change"), "data-on:change missing"
    assert kd, "data-on:keydown missing"
    assert "Tab" in kd
    assert "Escape" in kd


def test_render_combined_rows_attributes_are_well_formed() -> None:
    now = int(time.time())
    players = [PlayerData(id=1, discord_id=10, name="Alice")]
    chars = [
        (
            CharacterData(name="Aldric", player_id=1, initiative=15, last_used=now),
            "Alice",
        ),
        (
            CharacterData(name="Mira", player_id=1, initiative=None, last_used=now),
            "Alice",
        ),
    ]
    fragment = _render_combined_rows(
        chars, 1, frozenset(), "/roll", "/del", players, "/add"
    )
    elems = _collect(fragment)
    trs = [attrs for tag, attrs in elems if tag == "tr"]
    chars_with_data = [attrs["data-char"] for attrs in trs if "data-char" in attrs]
    assert "Aldric" in chars_with_data
    assert "Mira" in chars_with_data
    for attrs in trs:
        if "data-diceval" in attrs:
            val = attrs["data-diceval"] or ""
            assert '"' not in val, f"Unescaped quote in data-diceval: {val!r}"


def test_render_combined_rows_special_chars_in_names() -> None:
    """Characters with HTML-special names must not break attribute parsing."""
    now = int(time.time())
    players = [PlayerData(id=1, discord_id=10, name="Alice")]
    chars = [
        (
            CharacterData(name='D"Artagnan', player_id=1, initiative=10, last_used=now),
            "Alice",
        )
    ]
    fragment = _render_combined_rows(
        chars, 1, frozenset(), "/roll", "/del", players, "/add"
    )
    elems = _collect(fragment)
    trs = [attrs for tag, attrs in elems if tag == "tr"]
    assert any("data-char" in attrs for attrs in trs)
