# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import shutil
from unittest.mock import AsyncMock, MagicMock

import pytest

from initbot_core.state.factory import create_state_from_source
from tests.helpers import DATA_DIR, REFERENCE_FILES


def _make_json_state(tmp_path):
    for f in REFERENCE_FILES:
        shutil.copy(DATA_DIR / f, tmp_path / f)
    return create_state_from_source(f"json:{tmp_path}")


def _make_sqlite_state(tmp_path):
    db_path = tmp_path / "test.db"
    sqlite_state = create_state_from_source(f"sqlite:{db_path}")
    ref_dir = tmp_path / "ref"
    ref_dir.mkdir()
    for f in REFERENCE_FILES:
        shutil.copy(DATA_DIR / f, ref_dir / f)
    json_seed = create_state_from_source(f"json:{ref_dir}")
    sqlite_state.import_from(json_seed)
    return sqlite_state


@pytest.fixture(params=["json", "sqlite"], name="initbot_state")
def _initbot_state(request, tmp_path):
    if request.param == "json":
        return _make_json_state(tmp_path)
    return _make_sqlite_state(tmp_path)


@pytest.fixture(name="mock_ctx")
def _mock_ctx(initbot_state):
    ctx = MagicMock()
    ctx.author.name = "testuser"
    ctx.author.display_name = "testuser"
    ctx.bot.initbot_state = initbot_state
    ctx.send = AsyncMock(return_value=None)
    return ctx
