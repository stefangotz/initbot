# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import pytest

from initbot_core.utils import get_exact_or_unique_prefix_match


def test_ci_exact_match_resolves_ambiguous_prefix() -> None:
    """Case-insensitive exact match wins when prefix would be ambiguous."""
    candidates = ["Foo", "FooBar"]
    result = get_exact_or_unique_prefix_match("foo", candidates, str)
    assert result == "Foo"


def test_case_sensitive_exact_match_takes_priority() -> None:
    """Case-sensitive exact match still takes priority over ci exact match."""
    candidates = ["foo", "Foo"]
    result = get_exact_or_unique_prefix_match("foo", candidates, str)
    assert result == "foo"


def test_ci_exact_match_upper_to_lower() -> None:
    """Searching with 'FOO' resolves to 'foo' via case-insensitive exact match."""
    candidates = ["foo", "bar"]
    result = get_exact_or_unique_prefix_match("FOO", candidates, str)
    assert result == "foo"


def test_prefix_still_works_when_unambiguous() -> None:
    """Unique prefix match still works for the common case."""
    candidates = ["Mediocre Mel", "Brash Brad"]
    result = get_exact_or_unique_prefix_match("med", candidates, str)
    assert result == "Mediocre Mel"


def test_ambiguous_prefix_raises() -> None:
    """Ambiguous prefix with no ci exact match raises KeyError."""
    candidates = ["foo", "Foo"]
    with pytest.raises(KeyError):
        get_exact_or_unique_prefix_match("fo", candidates, str)
