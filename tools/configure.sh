#!/bin/sh

# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

set -ue

cd "$(dirname "$(realpath "${0}")")"/..

if ! command -v uv >/dev/null 2>&1; then
    ./tools/set_up_uv.sh
    export PATH="$HOME/.local/bin:$PATH"
fi

exec uv run tools/configure.py "$@"
