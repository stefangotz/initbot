# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Layout invariant tests for the tracker UI.

Each test encodes one of the invariants documented in the CSS comment block of
tracker.html. Failing tests mean a CSS or HTML change broke a stated invariant.

Viewport -> container width reference (body font 16px throughout):
  >= 480px viewport: padding = 24px each side -> container = viewport - 48px
  < 480px viewport: padding = 16px each side -> container = viewport - 32px

Container -> column disclosure (em breakpoints, 1em = 16px):
  container >= 513px  (>32em):  all 6 columns
  container 449-512px (28-32em): Player (col 3) hidden        -> 5 cols
  container 353-448px (22-28em): Player + Dice (col 4) hidden -> 4 cols
  container < 352px  (<22em):  + Delete (col 6) hidden        -> 3 cols

Test viewports chosen to land clearly within each zone:
  800px → container 632px (max-width cap) → 6 cols
  540px → container 492px → 5 cols
  450px → container 418px → 4 cols
  360px → container 328px → 3 cols
"""

import pytest
from playwright.sync_api import Page

pytestmark = pytest.mark.layout


# ── Invariant 1: No horizontal page scroll ─────────────────────────────────


@pytest.mark.parametrize("width", [320, 360, 450, 540, 600, 800])
def test_no_horizontal_scroll(tracker_page: Page, width: int) -> None:
    tracker_page.set_viewport_size({"width": width, "height": 720})
    scroll_w = tracker_page.evaluate("document.documentElement.scrollWidth")
    assert scroll_w <= width


# ── Invariant 2: Roll and Delete buttons always fully within the viewport ───


@pytest.mark.parametrize("width", [540, 800])
def test_buttons_within_viewport(tracker_page: Page, width: int) -> None:
    tracker_page.set_viewport_size({"width": width, "height": 720})
    bounds = tracker_page.evaluate(
        """(viewW) => [...document.querySelectorAll('.roll-btn, .del-btn')]
               .map(b => { const r = b.getBoundingClientRect();
                           return { left: r.left, right: r.right }; })""",
        width,
    )
    for btn in bounds:
        assert btn["left"] >= 0
        assert btn["right"] <= width


# ── Invariant 3: Character and Player columns equal width when both visible ─


def test_char_player_equal_width(tracker_page: Page) -> None:
    tracker_page.set_viewport_size({"width": 800, "height": 720})
    char_w, player_w = tracker_page.evaluate(
        """() => [
            document.querySelector('thead th:nth-child(2)').getBoundingClientRect().width,
            document.querySelector('thead th:nth-child(3)').getBoundingClientRect().width,
        ]"""
    )
    assert abs(char_w - player_w) < 2


# ── Invariant 4: Column thresholds scale proportionally with font size ──────


def test_columns_scale_with_zoom(tracker_page: Page) -> None:
    tracker_page.set_viewport_size({"width": 800, "height": 720})
    # At 16px root font, container ~632px >> 32em x 16=512px -- Player visible.
    tracker_page.evaluate("document.documentElement.style.fontSize = '16px'")
    assert tracker_page.locator("thead th:nth-child(3)").is_visible()
    # At 24px root font, 32em = 768px > 632px container — Player now hidden.
    tracker_page.evaluate("document.documentElement.style.fontSize = '24px'")
    assert not tracker_page.locator("thead th:nth-child(3)").is_visible()
    tracker_page.evaluate("document.documentElement.style.fontSize = ''")


# ── Progressive column disclosure ───────────────────────────────────────────


def test_all_columns_visible_at_wide_viewport(tracker_page: Page) -> None:
    tracker_page.set_viewport_size({"width": 800, "height": 720})
    for col in range(1, 7):
        assert tracker_page.locator(f"thead th:nth-child({col})").is_visible()


def test_player_hidden_at_medium_viewport(tracker_page: Page) -> None:
    # 540px → container 492px → 30.75em: Player hidden; Dice, Delete visible.
    tracker_page.set_viewport_size({"width": 540, "height": 720})
    assert not tracker_page.locator("thead th:nth-child(3)").is_visible()
    for col in [1, 2, 4, 5, 6]:
        assert tracker_page.locator(f"thead th:nth-child({col})").is_visible()


def test_dice_hidden_at_narrow_viewport(tracker_page: Page) -> None:
    # 450px → container 418px → 26.1em: Player + Dice hidden; Delete visible.
    tracker_page.set_viewport_size({"width": 450, "height": 720})
    for col in [3, 4]:
        assert not tracker_page.locator(f"thead th:nth-child({col})").is_visible()
    for col in [1, 2, 5, 6]:
        assert tracker_page.locator(f"thead th:nth-child({col})").is_visible()


def test_delete_hidden_at_very_narrow_viewport(tracker_page: Page) -> None:
    # 360px → container 328px → 20.5em: Player + Dice + Delete hidden.
    tracker_page.set_viewport_size({"width": 360, "height": 720})
    for col in [3, 4, 6]:
        assert not tracker_page.locator(f"thead th:nth-child({col})").is_visible()
    for col in [1, 2, 5]:
        assert tracker_page.locator(f"thead th:nth-child({col})").is_visible()


# ── Init, Character, Roll always visible ────────────────────────────────────


@pytest.mark.parametrize("width", [360, 450, 540, 800])
def test_permanent_columns_always_visible(tracker_page: Page, width: int) -> None:
    tracker_page.set_viewport_size({"width": width, "height": 720})
    for col in [1, 2, 5]:  # Init, Character, Roll
        assert tracker_page.locator(f"thead th:nth-child({col})").is_visible()


# ── Body font constant across breakpoints ───────────────────────────────────


def test_body_font_stable_across_breakpoints(tracker_page: Page) -> None:
    # Body font must not change when crossing the 480px viewport boundary,
    # because @container em breakpoints are relative to body font size.
    for width in [800, 360]:
        tracker_page.set_viewport_size({"width": width, "height": 720})
        font = tracker_page.evaluate("getComputedStyle(document.body).fontSize")
        assert font == "16px"


# ── Create-row: init and name inputs must not overlap ───────────────────────


def test_create_row_inputs_no_overlap(tracker_page: Page) -> None:
    tracker_page.set_viewport_size({"width": 800, "height": 720})
    tracker_page.click(".add-btn")
    tracker_page.wait_for_selector("#create-init-input")
    init_right, name_left = tracker_page.evaluate(
        """() => [
            document.getElementById('create-init-input').getBoundingClientRect().right,
            document.getElementById('create-name-input').getBoundingClientRect().left,
        ]"""
    )
    assert name_left >= init_right


# ── Touch: tap targets ≥ 44px (WCAG minimum) ───────────────────────────────


def test_tap_targets_touch(mobile_tracker_page: Page) -> None:
    for selector in [".roll-btn", ".del-btn", ".add-btn"]:
        height = mobile_tracker_page.evaluate(
            f"document.querySelector('{selector}').getBoundingClientRect().height"
        )
        assert height >= 44, f"{selector} tap target {height:.1f}px < 44px"
