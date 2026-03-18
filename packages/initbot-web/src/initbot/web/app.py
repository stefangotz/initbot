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

from pathlib import Path

import uvicorn
from starlette.applications import Starlette
from starlette.templating import Jinja2Templates

from initbot.state.factory import create_state_from_source

from initbot.web.config import WebSettings
from initbot.web.routes.tracker import make_routes


def create_app(settings: WebSettings | None = None) -> Starlette:
    cfg = settings or WebSettings()
    if not cfg.state.startswith("sqlite:"):
        raise SystemExit(f"initbot-web requires a SQLite state URI. Got: {cfg.state!r}")
    state = create_state_from_source(cfg.state)
    templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
    return Starlette(routes=make_routes(state, templates, cfg.web_secret))


def run() -> None:
    cfg = WebSettings(_cli_parse_args=True)  # type: ignore
    print(f"URL: http://localhost:{cfg.web_port}/s/{cfg.web_secret}/")
    uvicorn.run(create_app(cfg), host="0.0.0.0", port=cfg.web_port)
