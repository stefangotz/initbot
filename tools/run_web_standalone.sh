#!/bin/sh

# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

set -ue

# Local-only web server. For public access use run_web_ngrok.sh or run_compose.sh.
cd "$(dirname "$(realpath "${0}")")"/..
exec sh ./tools/run.sh initbot-web "$@"
