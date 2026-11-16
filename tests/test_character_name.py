# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import pytest

from initbot_core.character_name import validate_character_name


class TestValidNames:
    def test_plain_ascii(self) -> None:
        assert validate_character_name("Aragorn") == "Aragorn"

    def test_apostrophe(self) -> None:
        assert validate_character_name("O'Brian") == "O'Brian"

    def test_hyphen(self) -> None:
        assert validate_character_name("Anne-Marie") == "Anne-Marie"

    def test_accented_chars(self) -> None:
        assert validate_character_name("Éloise") == "Éloise"
        assert validate_character_name("Müller") == "Müller"

    def test_emoji(self) -> None:
        assert validate_character_name("🐉") == "🐉"

    def test_mixed_emoji_and_text(self) -> None:
        assert validate_character_name("Müller 🐉") == "Müller 🐉"

    def test_strips_leading_trailing_whitespace(self) -> None:
        assert validate_character_name("  Aragorn  ") == "Aragorn"

    def test_exactly_32_grapheme_clusters(self) -> None:
        name = "a" * 32
        assert validate_character_name(name) == name

    def test_exactly_32_clusters_with_emoji(self) -> None:
        # 31 letters + 1 emoji = 32 grapheme clusters
        name = "a" * 31 + "🐉"
        assert validate_character_name(name) == name

    def test_empty_after_strip_returns_empty(self) -> None:
        # Empty names are allowed through (callers produce their own error)
        assert validate_character_name("   ") == ""

    def test_discord_markdown_allowed(self) -> None:
        assert validate_character_name("**Bold** _Name_") == "**Bold** _Name_"

    def test_punctuation_allowed(self) -> None:
        assert validate_character_name("Dr. J. Watson, Jr.") == "Dr. J. Watson, Jr."

    def test_unicode_letters(self) -> None:
        assert validate_character_name("Иван") == "Иван"
        assert validate_character_name("李明") == "李明"


class TestLengthLimit:
    def test_33_grapheme_clusters_rejected(self) -> None:
        name = "a" * 33
        with pytest.raises(ValueError, match="32 characters or fewer"):
            validate_character_name(name)

    def test_33_clusters_with_emoji(self) -> None:
        name = "a" * 32 + "🐉"
        with pytest.raises(ValueError, match="32 characters or fewer"):
            validate_character_name(name)

    def test_emoji_counts_as_one_cluster(self) -> None:
        # 🐉 is 2 codepoints (U+1F409) but 1 grapheme cluster — 32 emoji should pass
        name = "🐉" * 32
        assert validate_character_name(name) == name

    def test_combined_emoji_counts_as_one_cluster(self) -> None:
        # Family emoji: multiple codepoints, 1 grapheme cluster
        family = "\U0001f468\u200d\U0001f469\u200d\U0001f467"
        name = family * 32
        assert validate_character_name(name) == name


class TestControlCharacters:
    def test_null_byte_rejected(self) -> None:
        with pytest.raises(ValueError, match="control character"):
            validate_character_name("Bad\x00Name")

    def test_newline_rejected(self) -> None:
        with pytest.raises(ValueError, match="control character"):
            validate_character_name("Bad\nName")

    def test_tab_rejected(self) -> None:
        with pytest.raises(ValueError, match="control character"):
            validate_character_name("Bad\tName")

    def test_del_rejected(self) -> None:
        with pytest.raises(ValueError, match="control character"):
            validate_character_name("Bad\x7fName")

    def test_lowest_control_char_rejected(self) -> None:
        with pytest.raises(ValueError, match="control character"):
            validate_character_name("\x01Name")


class TestBidiOverrides:
    def test_right_to_left_override_rejected(self) -> None:
        with pytest.raises(ValueError, match="bidirectional override"):
            validate_character_name("Bad\u202eName")

    def test_left_to_right_override_rejected(self) -> None:
        with pytest.raises(ValueError, match="bidirectional override"):
            validate_character_name("Bad\u202aName")

    def test_pop_directional_formatting_rejected(self) -> None:
        with pytest.raises(ValueError, match="bidirectional override"):
            validate_character_name("Bad\u202cName")

    def test_first_isolate_override_rejected(self) -> None:
        with pytest.raises(ValueError, match="bidirectional override"):
            validate_character_name("Bad\u2066Name")

    def test_last_isolate_override_rejected(self) -> None:
        with pytest.raises(ValueError, match="bidirectional override"):
            validate_character_name("Bad\u2069Name")


class TestZeroWidthChars:
    def test_zero_width_space_rejected(self) -> None:
        with pytest.raises(ValueError, match="zero-width"):
            validate_character_name("Bad\u200bName")

    def test_zero_width_non_joiner_rejected(self) -> None:
        with pytest.raises(ValueError, match="zero-width"):
            validate_character_name("Bad\u200cName")

    def test_zero_width_joiner_rejected(self) -> None:
        # ZWJ used standalone (not as part of a valid grapheme sequence) is rejected
        with pytest.raises(ValueError, match="zero-width"):
            validate_character_name("Bad\u200dName")

    def test_word_joiner_rejected(self) -> None:
        with pytest.raises(ValueError, match="zero-width"):
            validate_character_name("Bad\u2060Name")

    def test_bom_rejected(self) -> None:
        with pytest.raises(ValueError, match="zero-width"):
            validate_character_name("\ufeffName")


class TestPrivateUseArea:
    def test_pua_basic_rejected(self) -> None:
        with pytest.raises(ValueError, match="private-use"):
            validate_character_name("Bad\ue000Name")

    def test_pua_end_rejected(self) -> None:
        with pytest.raises(ValueError, match="private-use"):
            validate_character_name("Bad\uf8ffName")

    def test_supplementary_pua_rejected(self) -> None:
        with pytest.raises(ValueError, match="private-use"):
            validate_character_name("Bad\U000f0000Name")
