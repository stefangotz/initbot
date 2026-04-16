# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import shutil
from pathlib import Path

from initbot_core.state.factory import create_state_from_source

_DATA_DIR = Path(__file__).parent / "data"


def _check_state(state) -> None:
    assert state is not None
    assert state.characters is not None
    assert len(state.characters.get_all()) == 1


def test_load_sqlite(tmp_path):
    db_copy = tmp_path / "test.sqlite"
    shutil.copy2(_DATA_DIR / "test.sqlite", db_copy)
    state = create_state_from_source(f"sqlite:{db_copy}")
    _check_state(state)
