# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# pylint: disable=redefined-outer-name  # standard pytest fixture injection pattern

import socket
import subprocess
import threading
import time
import urllib.request
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from typing import Final

import pytest
import pytest_asyncio
import uvicorn
from playwright.async_api import Browser, Page, async_playwright

from initbot_core.config import CORE_CFG
from initbot_core.data.character import NewCharacterData
from initbot_core.state.factory import create_state_from_source
from initbot_web.app import create_app
from initbot_web.config import WebSettings

_PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]
_DATASTAR_BUNDLE: Final = (
    _PROJECT_ROOT / "packages/initbot-web/src/initbot_web/static/datastar.js"
)
_VENDOR_WEB_ASSETS: Final = _PROJECT_ROOT / "tools/vendor-web-assets.sh"


def _free_tcp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _free_udp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _seed_state(db_path: Path) -> None:
    """Populate db with the same sample data as run_web_standalone_dev.sh."""
    state = create_state_from_source(f"sqlite:{db_path}")
    now = int(time.time())

    players_raw = [
        (1001, "Stefan"),
        (1002, "Anna"),
        (1003, "Bob"),
        (1004, "Carol"),
        (1005, "Dave"),
        (1006, "Eve"),
    ]
    players = [
        state.players.upsert_discord(discord_id=did, name=name)
        for did, name in players_raw
    ]

    characters_raw = [
        ("Aldric", 0, 18, "d20+2"),
        ("Mira", 1, 15, "d20+1"),
        ("Brother Thog", 2, 15, "d20"),
        ("Elara", 3, 9, "d20-1"),
        ("Zyx", 4, 3, "d20-2"),
        ("Tara", 5, None, None),
    ]
    for name, player_idx, initiative, initiative_dice in characters_raw:
        state.characters.add_store_and_get(
            NewCharacterData(
                name=name,
                player_id=players[player_idx].id,
                initiative=initiative,
                initiative_dice=initiative_dice,
                last_used=now,
            )
        )


@pytest.fixture(scope="session")
def vendored_web_assets(request: pytest.FixtureRequest) -> None:
    """Vendor ignored frontend assets when running layout tests from a fresh checkout."""
    if _DATASTAR_BUNDLE.is_file():
        return

    terminal_reporter = request.config.pluginmanager.get_plugin("terminalreporter")
    if terminal_reporter is not None:
        terminal_reporter.write_line(
            "Datastar bundle is missing; running tools/vendor-web-assets.sh."
        )

    # The command is fixed to this repository's checked-in helper.
    result = subprocess.run(  # noqa: S603
        [str(_VENDOR_WEB_ASSETS)],
        cwd=_PROJECT_ROOT,
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode != 0 or not _DATASTAR_BUNDLE.is_file():
        output = "\n".join(part for part in (result.stdout, result.stderr) if part)
        pytest.fail(
            "Could not prepare the Datastar bundle required by the layout tests. "
            "Run `tools/vendor-web-assets.sh` manually and retry."
            + (f"\nVendoring output:\n{output}" if output else ""),
            pytrace=False,
        )


@pytest.fixture(scope="session")
def live_server_url(
    vendored_web_assets: None,  # pylint: disable=unused-argument
    tmp_path_factory: pytest.TempPathFactory,
) -> Generator[str]:
    db_path = tmp_path_factory.mktemp("layout") / "layout.db"
    _seed_state(db_path)

    # Plain HTTP — no Secure cookies so the browser session works without TLS.
    CORE_CFG.web_hostname = ""

    port = _free_tcp_port()
    settings = WebSettings(
        state=f"sqlite:{db_path}",
        web_port=port,
        notify_port=_free_udp_port(),
    )
    app = create_app(settings, web_url_path_prefix="layout")

    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    for _ in range(50):
        try:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/layout/join/", timeout=1
            ):
                break
        except OSError:
            time.sleep(0.1)
    else:
        raise RuntimeError("Layout test server did not start in time")

    yield f"http://127.0.0.1:{port}/layout"

    server.should_exit = True
    thread.join(timeout=5)


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def browser(
    browser_name: str, browser_type_launch_args: dict[str, object]
) -> AsyncGenerator[Browser]:
    async with async_playwright() as playwright:
        browser_type = getattr(playwright, browser_name)
        browser_instance = await browser_type.launch(**browser_type_launch_args)
        yield browser_instance
        await browser_instance.close()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def auth_cookies(live_server_url: str, browser: Browser) -> list:
    """Join once and capture session cookies for reuse across all layout tests."""
    context = await browser.new_context()
    try:
        page = await context.new_page()
        await page.goto(f"{live_server_url}/join/")
        await page.fill("input[type=text]", "LayoutTestUser")
        await page.click("button[type=submit]")
        await page.wait_for_url("**/tracker/")
        return await context.cookies()
    finally:
        await context.close()


@pytest_asyncio.fixture(loop_scope="session")
async def tracker_page(
    live_server_url: str, browser: Browser, auth_cookies: list
) -> AsyncGenerator[Page]:
    """Authenticated page at the tracker, with SSE rows loaded."""
    context = await browser.new_context()
    try:
        await context.add_cookies(auth_cookies)
        page = await context.new_page()
        await page.goto(f"{live_server_url}/tracker/")
        await page.wait_for_selector("#char-rows tr")
        yield page
    finally:
        await context.close()


@pytest_asyncio.fixture(loop_scope="session")
async def mobile_tracker_page(
    live_server_url: str, browser: Browser, auth_cookies: list
) -> AsyncGenerator[Page]:
    """Authenticated page in a touch-emulating context (triggers @media hover:none)."""
    context = await browser.new_context(
        has_touch=True,
        is_mobile=True,
        viewport={"width": 390, "height": 844},
    )
    try:
        await context.add_cookies(auth_cookies)
        page = await context.new_page()
        await page.goto(f"{live_server_url}/tracker/")
        await page.wait_for_selector("#char-rows tr")
        yield page
    finally:
        await context.close()
