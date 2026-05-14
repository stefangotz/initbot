#!/bin/sh

# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

set -ue

cd "$(dirname "$(realpath "${0}")")"/..

sh ./tools/set_up_uv.sh
uv sync
cmd="$1"; shift
exec uv run "$cmd" "$@"
