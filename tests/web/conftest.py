# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import pytest

from initbot_core.config import CORE_CFG


@pytest.fixture(autouse=True)
def _clear_domain(monkeypatch):
    # Ensure https_only=False for all web tests so the httpx TestClient
    # (http://testserver) sends session cookies. A DOMAIN set in .env would
    # make cookies Secure, which httpx won't send over plain HTTP.
    monkeypatch.setattr(CORE_CFG, "domain", "")
