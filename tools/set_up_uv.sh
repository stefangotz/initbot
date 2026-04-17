#!/bin/sh

# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

set -ue

if ! which uv; then
	curl -LsSf https://github.com/astral-sh/uv/releases/download/0.11.7/uv-installer.sh | sh
	which uv > /dev/null
fi
