# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from starlette.testclient import TestClient

from initbot_web.app import create_app
from initbot_web.config import WebSettings


def test_tracker_page(tmp_path):
    settings = WebSettings(
        state=f"sqlite:{tmp_path / 'test.db'}",
        web_secret="testsecret",
    )
    app = create_app(settings)
    with TestClient(app) as client:
        resp = client.get("/s/testsecret/")
        assert resp.status_code == 200
        assert "Initiative Order" in resp.text
        assert "testsecret" in resp.text


def test_wrong_secret_returns_404(tmp_path):
    settings = WebSettings(
        state=f"sqlite:{tmp_path / 'test.db'}",
        web_secret="testsecret",
    )
    app = create_app(settings)
    with TestClient(app) as client:
        assert client.get("/s/wrongsecret/").status_code == 404
