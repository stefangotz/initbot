#!/bin/sh

# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

set -ue

output=$(docker run --rm initbot-web 2>&1) || true
echo "$output"
echo "$output" | grep -qF "initbot-web requires a SQLite state URI"
