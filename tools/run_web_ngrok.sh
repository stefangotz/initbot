#!/bin/sh

# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

set -ue

cd "$(dirname "$(realpath "${0}")")"/..

# shellcheck source=/dev/null
[ -f .env ] && . ./.env

if [ -z "${DOMAIN:-}" ]; then
    printf 'Error: DOMAIN is not set. Run sh ./tools/configure.sh first.\n' >&2
    exit 1
fi

NGROK_PID=""
WEB_PID=""

cleanup() {
    if [ -n "$NGROK_PID" ]; then
        kill "$NGROK_PID" 2>/dev/null || true
    fi
    if [ -n "$WEB_PID" ]; then
        kill "$WEB_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT INT TERM

ngrok http --url "https://${DOMAIN}" 8080 > /tmp/ngrok-initbot.log 2>&1 &
NGROK_PID=$!

printf 'Waiting for ngrok tunnel...\n'
ATTEMPTS=0
TUNNEL_URL=""
while [ "$ATTEMPTS" -lt 30 ]; do
    TUNNEL_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null \
        | python3 -c "
import json, sys
data = json.load(sys.stdin)
for t in data.get('tunnels', []):
    url = t.get('public_url', '')
    if url.startswith('https://'):
        print(url)
        break
" 2>/dev/null || true)
    [ -n "$TUNNEL_URL" ] && break
    ATTEMPTS=$((ATTEMPTS + 1))
    sleep 1
done

if [ -z "$TUNNEL_URL" ]; then
    printf 'Error: ngrok tunnel did not start within 30 seconds.\n' >&2
    printf 'Check /tmp/ngrok-initbot.log for details.\n' >&2
    exit 1
fi

printf 'Tunnel: %s\n' "$TUNNEL_URL"

sh ./tools/run_web.sh &
WEB_PID=$!

wait "$WEB_PID"
