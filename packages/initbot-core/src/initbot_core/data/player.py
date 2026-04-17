# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from dataclasses import dataclass


@dataclass
class PlayerData:
    id: int  # Internal primary key, auto-assigned, used as foreign key by other entities
    discord_id: int  # Discord snowflake
    name: str  # Display name, refreshed on each command invocation
