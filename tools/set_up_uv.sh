#!/bin/sh

# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

set -ue

if ! which uv; then
	curl -LsSf https://astral.sh/uv/install.sh | sh
	which uv > /dev/null
fi
