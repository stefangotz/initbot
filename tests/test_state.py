# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later


from pathlib import Path

from initbot_core.state.factory import create_state_from_source


def _check_state(state) -> None:
    assert state is not None
    assert state.characters is not None
    assert len(state.characters.get_all()) == 1


def test_load_json():
    state = create_state_from_source(f"json:{Path(__file__).parent / 'data'}")
    _check_state(state)


def test_load_sqlite():
    state = create_state_from_source(
        f"sqlite:{Path(__file__).parent / 'data' / 'test.sqlite'}"
    )
    _check_state(state)
