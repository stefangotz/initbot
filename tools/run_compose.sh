#!/bin/sh

# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

set -ue

REPO_DIR="$(cd "$(dirname "$(realpath "${0}")")"/.. && pwd)"
cd "$REPO_DIR"

usage() {
    printf 'Usage: %s [caddy|ngrok]\n' "$0" >&2
    printf '\n' >&2
    printf '  caddy  HTTPS via Caddy reverse proxy (requires DOMAIN in .env)\n' >&2
    printf '  ngrok  HTTPS via ngrok tunnel (requires DOMAIN and NGROK_AUTHTOKEN in .env)\n' >&2
    printf '\n' >&2
    printf 'If no argument is given the profile is auto-detected from .env:\n' >&2
    printf '  NGROK_AUTHTOKEN present -> ngrok\n' >&2
    printf '  otherwise               -> caddy\n' >&2
}

if [ $# -gt 0 ]; then
    case "$1" in
        caddy | ngrok)
            PROFILE="$1"
            ;;
        -h | --help)
            usage
            exit 0
            ;;
        *)
            usage
            exit 1
            ;;
    esac
else
    # shellcheck source=/dev/null
    [ -f .env ] && . ./.env
    if [ -n "${NGROK_AUTHTOKEN:-}" ]; then
        PROFILE="ngrok"
    else
        PROFILE="caddy"
    fi
    printf 'Profile: %s  (pass caddy or ngrok to override)\n' "$PROFILE"
fi

docker compose build
exec docker compose --profile "$PROFILE" up
