#!/bin/sh

# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

set -ue

cd "$(dirname "$(realpath "${0}")")"/../..

tools/run_web_dev.sh &
WEB_PID=$!
trap 'kill "$WEB_PID" 2>/dev/null || true; wait "$WEB_PID" 2>/dev/null || true' EXIT

for i in $(seq 1 30); do
    if curl -s -o /dev/null http://localhost:8080/; then
        echo "Web server started successfully after ${i}s"
        exit 0
    fi
    sleep 1
done

echo "Web server failed to start within 30 seconds"
exit 1
