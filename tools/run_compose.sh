#!/bin/sh

# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

set -ue

REPO_DIR="$(cd "$(dirname "$(realpath "${0}")")"/.. && pwd)"
cd "$REPO_DIR"
docker compose build
exec docker compose up
