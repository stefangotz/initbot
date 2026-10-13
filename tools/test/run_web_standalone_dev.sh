#!/bin/sh

# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

set -ue

cd "$(dirname "$(realpath "${0}")")"/../..

./tools/prep_web_standalone_dev.sh
./tools/run_web_standalone_dev.sh &
WEB_PID=$!
trap 'kill "$WEB_PID" 2>/dev/null || true; wait "$WEB_PID" 2>/dev/null || true' EXIT

for I in $(seq 1 30); do
    echo "Waited ${I}s for server startup..."
    if curl -s -o /dev/null http://localhost:8080/; then
        echo "Web server started successfully after ${I}s"
        exit 0
    fi
    sleep 1
done

echo "Web server failed to start within 30 seconds"
exit 1
