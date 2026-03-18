#!/bin/sh

# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

set -ue

cd "$(dirname "$(realpath "${0}")")"/..

if ! which uv; then
	curl -LsSf https://astral.sh/uv/install.sh | sh
	export PATH="$PATH:$HOME/.cargo/bin"
	which uv > /dev/null
else
	uv self update
fi
deactivate || true
rm -fr .venv
uv sync
. ./.venv/bin/activate
pre-commit install
