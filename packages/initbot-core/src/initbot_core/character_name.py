# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import grapheme

_MAX_GRAPHEME_CLUSTERS = 32

# Unicode bidi override characters that can spoof displayed text
_BIDI_OVERRIDES = frozenset(range(0x202A, 0x202F)) | frozenset(range(0x2066, 0x206A))

# Zero-width and invisible characters that make names look identical but differ.
# ZWJ (U+200D) is allowed within emoji grapheme sequences (e.g. 👨‍👩‍👧) — see below.
_ZERO_WIDTH = frozenset({0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF})

# Private Use Area ranges (render unpredictably across systems)
_PRIVATE_USE_RANGES = [(0xE000, 0xF8FF), (0xF0000, 0xFFFFF), (0x100000, 0x10FFFF)]

# Emoji codepoints start around here; used to identify ZWJ in emoji sequences
_EMOJI_RANGE_START = 0x1F000


def _is_private_use(cp: int) -> bool:
    return any(lo <= cp <= hi for lo, hi in _PRIVATE_USE_RANGES)


def _cluster_contains_emoji(cluster: str) -> bool:
    return any(ord(ch) >= _EMOJI_RANGE_START for ch in cluster)


def _check_clusters(name: str) -> tuple[str | None, int]:
    """Return (rejection_reason_or_None, grapheme_cluster_count) in a single pass."""
    count = 0
    for cluster in grapheme.graphemes(name):
        count += 1
        is_emoji_sequence = len(cluster) > 1 and _cluster_contains_emoji(cluster)
        for ch in cluster:
            cp = ord(ch)
            if cp <= 0x1F or cp == 0x7F:
                return f"control character U+{cp:04X}", count
            if cp in _BIDI_OVERRIDES:
                return f"bidirectional override character U+{cp:04X}", count
            if cp in _ZERO_WIDTH and not (is_emoji_sequence and cp == 0x200D):
                return f"zero-width or invisible character U+{cp:04X}", count
            if _is_private_use(cp):
                return f"private-use codepoint U+{cp:04X}", count
    return None, count


def validate_character_name(name: str) -> str:
    """Validate and normalise a character name.

    Strips leading/trailing whitespace, then checks for invalid content.
    Returns the stripped name on success, or raises ValueError with a
    user-facing message describing the problem.
    """
    name = name.strip()
    if not name:
        return name  # callers check for empty; let them produce their own message

    rejected, cluster_count = _check_clusters(name)
    if rejected is not None:
        raise ValueError(f"Character name contains a {rejected}, which is not allowed.")
    if cluster_count > _MAX_GRAPHEME_CLUSTERS:
        raise ValueError(
            f"Name must be {_MAX_GRAPHEME_CLUSTERS} characters or fewer "
            f"(got {cluster_count})."
        )

    return name
