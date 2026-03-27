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
characters = [
    {"name": "Aldric",       "user": "Stefan", "active": True, "initiative": 18, "initiative_time": now, "last_used": now},
    {"name": "Mira",         "user": "Anna",   "active": True, "initiative": 15, "initiative_time": now, "last_used": now},
    {"name": "Brother Thog", "user": "Bob",    "active": True, "initiative": 15, "initiative_time": now, "last_used": now},
    {"name": "Elara",        "user": "Carol",  "active": True, "initiative":  9, "initiative_time": now, "last_used": now},
    {"name": "Zyx",          "user": "Dave",   "active": True, "initiative":  3, "initiative_time": now, "last_used": now},
]
with open(f"{sys.argv[1]}/characters.json", "w") as f:
    json.dump({"characters": characters}, f)
PYEOF

mkdir -p dev-state
rm -f dev-state/dev.sqlite
uv run python -m initbot_core.state.export_json_to_sql_state "${DEV_JSON_DIR}" dev-state/dev.sqlite

exec uv run initbot-web --web_secret dev --web_port 8080 --state "sqlite:dev-state/dev.sqlite" "$@"
