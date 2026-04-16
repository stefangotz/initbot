#!/bin/sh

# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

set -ue

cd "$(dirname "$(realpath "${0}")")"/..

mkdir -p dev-state
rm -f dev-state/dev.sqlite

uv run python3 - dev-state/dev.sqlite <<'PYEOF'
import sys
import time

from initbot_core.data.character import NewCharacterData
from initbot_core.state.factory import create_state_from_source

state = create_state_from_source(f"sqlite:{sys.argv[1]}")
now = int(time.time())

players_raw = [
    (1001, "Stefan"),
    (1002, "Anna"),
    (1003, "Bob"),
    (1004, "Carol"),
    (1005, "Dave"),
    (1006, "Eve"),
]
players = [state.players.upsert(discord_id=did, name=name) for did, name in players_raw]

characters_raw = [
    ("Aldric",       0, 18, "d20+2"),
    ("Mira",         1, 15, "d20+1"),
    ("Brother Thog", 2, 15, "d20"),
    ("Elara",        3,  9, "d20-1"),
    ("Zyx",          4,  3, "d20-2"),
    ("Tara",         5, None, None),
]
for name, player_idx, initiative, initiative_dice in characters_raw:
    state.characters.add_store_and_get(
        NewCharacterData(
            name=name,
            player_id=players[player_idx].id,
            initiative=initiative,
            initiative_dice=initiative_dice,
            last_used=now,
        )
    )
PYEOF

exec env WEB_URL_PATH_PREFIX=dev uv run initbot-web --web_port 8080 --state "sqlite:dev-state/dev.sqlite" "$@"
