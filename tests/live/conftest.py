# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import asyncio
import contextlib
import os

import discord
import pytest

_TOKEN = os.environ.get("TOKEN", "_test_token_")


@pytest.fixture(autouse=True)
def require_live_token():
    if _TOKEN == "_test_token_":
        pytest.skip("Live Discord bot token not available (set TOKEN env var)")


@pytest.fixture
async def live_bot():
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)

    ready = asyncio.Event()

    @client.event
    async def on_ready():
        ready.set()

    task = asyncio.create_task(client.start(_TOKEN))
    await asyncio.wait_for(ready.wait(), timeout=30.0)

    yield client

    await client.close()
    with contextlib.suppress(Exception):
        await asyncio.wait_for(task, timeout=5.0)
