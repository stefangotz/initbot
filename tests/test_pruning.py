# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import time

from initbot_core.data.character import CharacterData, is_eligible_for_pruning

THRESHOLD = 90


def test_eligible_when_last_used_is_none():
    cdi = CharacterData(name="X", user="alice")
    assert is_eligible_for_pruning(cdi, THRESHOLD)


def test_eligible_when_last_used_is_old():
    old_ts = int(time.time()) - (THRESHOLD + 1) * 86400
    cdi = CharacterData(name="X", user="alice", last_used=old_ts)
    assert is_eligible_for_pruning(cdi, THRESHOLD)


def test_not_eligible_when_last_used_is_recent():
    recent_ts = int(time.time())
    cdi = CharacterData(name="X", user="alice", last_used=recent_ts)
    assert not is_eligible_for_pruning(cdi, THRESHOLD)
