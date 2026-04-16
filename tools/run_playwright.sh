#!/bin/sh

# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# Start the Playwright MCP server outside the nono sandbox.
# Run this in a separate terminal before starting Claude Code with nono.
# The server listens on http://localhost:8931/sse and Claude Code connects
# to it via SSE transport, bypassing sandbox restrictions on browser processes.

set -ue

exec npx --yes @playwright/mcp@latest --headless --isolated --browser chrome --port 8931
