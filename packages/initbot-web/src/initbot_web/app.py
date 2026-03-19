# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from pathlib import Path

import uvicorn
from starlette.applications import Starlette
from starlette.templating import Jinja2Templates

from initbot_core.state.factory import create_state_from_source

from initbot_web.config import WebSettings
from initbot_web.routes.tracker import make_routes


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
