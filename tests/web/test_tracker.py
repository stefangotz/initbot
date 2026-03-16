# Copyright 2026 Stefan Götz <github.nooneelse@spamgourmet.com>

# This file is part of initbot.

# initbot is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.

# initbot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU Affero General Public
# License along with initbot. If not, see <https://www.gnu.org/licenses/>.

from starlette.testclient import TestClient

from initbot.web.app import create_app
from initbot.web.config import WebSettings


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
