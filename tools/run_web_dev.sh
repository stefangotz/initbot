#!/bin/sh

# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

set -ue

cd "$(dirname "$(realpath "${0}")")"/..

DEV_JSON_DIR="$(mktemp -d)"
trap 'rm -rf "${DEV_JSON_DIR}"' EXIT

python3 - "${DEV_JSON_DIR}" <<'PYEOF'
import json, sys, time
now = int(time.time())
players = [
    {"id": 1, "discord_id": 1001, "name": "Stefan"},
    {"id": 2, "discord_id": 1002, "name": "Anna"},
    {"id": 3, "discord_id": 1003, "name": "Bob"},
    {"id": 4, "discord_id": 1004, "name": "Carol"},
    {"id": 5, "discord_id": 1005, "name": "Dave"},
    {"id": 6, "discord_id": 1006, "name": "Eve"},
]
characters = [
    {"name": "Aldric",       "player_id": 1, "initiative": 18, "initiative_dice": "d20+2", "last_used": now},
    {"name": "Mira",         "player_id": 2, "initiative": 15, "initiative_dice": "d20+1", "last_used": now},
    {"name": "Brother Thog", "player_id": 3, "initiative": 15, "initiative_dice": "d20",   "last_used": now},
    {"name": "Elara",        "player_id": 4, "initiative":  9, "initiative_dice": "d20-1", "last_used": now},
    {"name": "Zyx",          "player_id": 5, "initiative":  3, "initiative_dice": "d20-2", "last_used": now},
    {"name": "Tara",         "player_id": 6,                                                "last_used": now},
]
with open(f"{sys.argv[1]}/players.json", "w") as f:
    json.dump({"players": players}, f)
with open(f"{sys.argv[1]}/characters.json", "w") as f:
    json.dump({"characters": characters}, f)
PYEOF

mkdir -p dev-state
rm -f dev-state/dev.sqlite
uv run python -m initbot_core.state.export_json_to_sql_state "${DEV_JSON_DIR}" dev-state/dev.sqlite

exec env WEB_URL_PATH_PREFIX=dev uv run initbot-web --web_port 8080 --state "sqlite:dev-state/dev.sqlite" "$@"
