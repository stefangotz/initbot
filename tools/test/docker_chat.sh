#!/bin/sh

# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

set -ue

output=$(docker run --rm initbot-chat --token 123 2>&1) || true
echo "$output"
echo "$output" | grep -qF "discord.errors.LoginFailure"
