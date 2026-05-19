# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
from pathlib import Path

from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

_STATIC = Path(__file__).parent.parent / "static"
_ICONS = Path(__file__).parent.parent / "icons"


def make_pwa_routes(url_path_prefix: str) -> list[Route | Mount]:
    manifest_json = json.dumps({
        "name": "Initiative Tracker",
        "short_name": "Initiative",
        "scope": "/",
        "start_url": f"/{url_path_prefix}/join/",
        "display": "standalone",
        "background_color": "#f5f0e8",
        "theme_color": "#b8860b",
        "icons": [
            {"src": "/icons/192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/icons/512.png", "sizes": "512x512", "type": "image/png"},
        ],
    })
    sw_js = (_STATIC / "sw.js").read_text()

    async def _manifest(_request: Request) -> Response:
        return Response(
            manifest_json,
            media_type="application/manifest+json",
            headers={"Cache-Control": "no-cache"},
        )

    async def _sw(_request: Request) -> Response:
        return Response(
            sw_js,
            media_type="application/javascript",
            headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"},
        )

    return [
        Route("/manifest.json", _manifest),
        Route("/sw.js", _sw),
        Mount("/icons", StaticFiles(directory=_ICONS)),
        Mount("/static", StaticFiles(directory=_STATIC)),
    ]
