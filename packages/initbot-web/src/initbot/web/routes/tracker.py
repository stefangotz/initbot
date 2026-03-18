# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import asyncio
import re
from datetime import datetime

from datastar_py import ServerSentEventGenerator as SSE
from datastar_py.starlette import datastar_response
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route
from starlette.templating import Jinja2Templates

from initbot.models.character import Character
from initbot.state.state import State

POLL_INTERVAL = 1.5
STALE_SECONDS = 24 * 3600


def make_routes(state: State, templates: Jinja2Templates, secret: str) -> list[Route]:
    async def tracker_page(request: Request) -> Response:
        return templates.TemplateResponse(request, "tracker.html", {"secret": secret})

    @datastar_response
    async def tracker_sse(request: Request):
        last_snapshot: tuple[tuple[str, int | None], ...] = ()
        while not await request.is_disconnected():
            now = int(datetime.now().timestamp())
            chars = [
                Character(c, state)
                for c in state.characters.get_all()
                if c.active
                and c.initiative_time is not None
                and c.initiative_time > now - STALE_SECONDS
            ]
            chars.sort(key=lambda c: c.initiative_comparison_value(), reverse=True)

            snapshot = tuple((c.name, c.initiative) for c in chars)
            if snapshot != last_snapshot:
                last_snapshot = snapshot
                yield SSE.patch_elements(_render_rows(chars))

            await asyncio.sleep(POLL_INTERVAL)

    return [
        Route(f"/s/{secret}/", tracker_page),
        Route(f"/s/{secret}/sse", tracker_sse),
    ]


def _render_rows(chars: list[Character]) -> str:
    rows = "".join(
        f'<tr id="r{i}"><td>{i + 1}</td><td>{_safe_int(c.initiative)}</td>'
        f"<td>{_safe_str(c.name)}</td><td>{_safe_str(c.user)}</td></tr>"
        for i, c in enumerate(chars)
    )
    return f'<tbody id="initiative-rows">{rows}</tbody>'


def _safe_int(value: int | None) -> str:
    return re.sub(r"[^\d]", "", str(value))


def _safe_str(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9\xc0-\xd6\xd8-\xf6\xf8-\xff ]", "", value)
