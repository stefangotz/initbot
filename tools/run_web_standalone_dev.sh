#!/bin/sh

# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

set -ue

# Dev server with synthetic sample data. Not for production use.
cd "$(dirname "$(realpath "${0}")")"/..

./tools/prep_web_standalone_dev.sh

exec env WEB_URL_PATH_PREFIX=dev WEB_HOSTNAME= uv run initbot-web --web_port 8080 --state "sqlite:dev-state/dev.sqlite" "$@"
