# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import secrets
import sqlite3
import time
from collections.abc import Sequence
from pathlib import Path

from initbot_core.config import CORE_CFG
from initbot_core.data.character import CharacterData, NewCharacterData
from initbot_core.data.player import PlayerData
from initbot_core.state.state import (
    _WEB_LOGIN_TOKEN_TTL,
    CharacterActionState,
    CharacterState,
    PlayerState,
    SessionSecretState,
    State,
    WebLoginTokenState,
)
from initbot_core.state.validation import check_state_directory

_CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS _sqlcharacterdata (
    name TEXT NOT NULL PRIMARY KEY,
    player_id INTEGER,
    initiative INTEGER,
    initiative_dice TEXT,
    last_used INTEGER
);
CREATE TABLE IF NOT EXISTS _sqlplayerdata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    discord_id INTEGER UNIQUE,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS _sqlcharacteraction (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_name TEXT NOT NULL,
    position INTEGER NOT NULL,
    template TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS _sqlweblogintoken (
    token TEXT PRIMARY KEY,
    discord_id INTEGER NOT NULL,
    expires_at INTEGER NOT NULL,
    used INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS _sqlsessionsecret (
    id INTEGER PRIMARY KEY,
    secret TEXT NOT NULL,
    expires_at INTEGER NOT NULL
);
"""


class _SqlCharacterState(CharacterState):
    def __init__(self, db: sqlite3.Connection) -> None:
        self._db = db

    def get_all(self) -> Sequence[CharacterData]:
        rows = self._db.execute(
            "SELECT name, player_id, initiative, initiative_dice, last_used"
            " FROM _sqlcharacterdata"
        ).fetchall()
        return [CharacterData(*row) for row in rows]

    def _add_store_and_get(self, char_data: NewCharacterData) -> CharacterData:
        last_used = (
            char_data.last_used if char_data.last_used is not None else int(time.time())
        )
        self._db.execute(
            "INSERT INTO _sqlcharacterdata (name, player_id, initiative, initiative_dice, last_used)"
            " VALUES (?, ?, ?, ?, ?)",
            (
                char_data.name,
                char_data.player_id,
                char_data.initiative,
                char_data.initiative_dice,
                last_used,
            ),
        )
        return CharacterData(
            name=char_data.name,
            player_id=char_data.player_id,
            initiative=char_data.initiative,
            initiative_dice=char_data.initiative_dice,
            last_used=last_used,
        )

    def _rename_and_store(
        self, char_data: CharacterData, new_name: str
    ) -> CharacterData:
        self._db.execute(
            "UPDATE _sqlcharacterdata SET name=? WHERE name=?",
            (new_name, char_data.name),
        )
        return CharacterData(
            name=new_name,
            player_id=char_data.player_id,
            initiative=char_data.initiative,
            initiative_dice=char_data.initiative_dice,
            last_used=char_data.last_used,
        )

    def update_and_store(self, char_data: CharacterData) -> None:
        self._db.execute(
            "UPDATE _sqlcharacterdata"
            " SET player_id=?, initiative=?, initiative_dice=?, last_used=?"
            " WHERE name=?",
            (
                char_data.player_id,
                char_data.initiative,
                char_data.initiative_dice,
                char_data.last_used,
                char_data.name,
            ),
        )

    def remove_and_store(self, char_data: CharacterData) -> None:
        self._db.execute(
            "DELETE FROM _sqlcharacterdata WHERE name=?",
            (char_data.name,),
        )


class _SqlPlayerState(PlayerState):
    def __init__(self, db: sqlite3.Connection) -> None:
        self._db = db

    def upsert(self, discord_id: int, name: str) -> PlayerData:
        row = self._db.execute(
            "INSERT INTO _sqlplayerdata (discord_id, name) VALUES (?, ?)"
            " ON CONFLICT(discord_id) DO UPDATE SET name=excluded.name"
            " RETURNING id, discord_id, name",
            (discord_id, name),
        ).fetchone()
        if row is None:
            raise RuntimeError("UPSERT into _sqlplayerdata returned no row")
        return PlayerData(*row)

    def get_from_id(self, player_id: int) -> PlayerData:
        row = self._db.execute(
            "SELECT id, discord_id, name FROM _sqlplayerdata WHERE id=?",
            (player_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"No player with id={player_id}")
        return PlayerData(*row)

    def get_from_discord_id(self, discord_id: int) -> PlayerData | None:
        row = self._db.execute(
            "SELECT id, discord_id, name FROM _sqlplayerdata WHERE discord_id=?",
            (discord_id,),
        ).fetchone()
        return PlayerData(*row) if row is not None else None

    def get_all(self) -> Sequence[PlayerData]:
        rows = self._db.execute(
            "SELECT id, discord_id, name FROM _sqlplayerdata"
        ).fetchall()
        return [PlayerData(*row) for row in rows]


class _SqlCharacterActionState(CharacterActionState):
    # No foreign-key constraint on character_name: adding PRAGMA foreign_keys=ON
    # to existing deployments risks breaking them. Referential integrity is
    # maintained at the command layer instead: initbot_chat.commands.character
    # calls remove_all_for_character() before deleting a character.
    def __init__(self, db: sqlite3.Connection) -> None:
        self._db = db

    def get_all_for_character(self, character_name: str) -> Sequence[str]:
        rows = self._db.execute(
            "SELECT template FROM _sqlcharacteraction WHERE character_name=? ORDER BY position",
            (character_name,),
        ).fetchall()
        return [row[0] for row in rows]

    def add(self, character_name: str, template: str) -> int:
        row = self._db.execute(
            "INSERT INTO _sqlcharacteraction (character_name, position, template)"
            " VALUES (?, (SELECT COUNT(*) FROM _sqlcharacteraction WHERE character_name=?), ?)"
            " RETURNING position + 1",
            (character_name, character_name, template),
        ).fetchone()
        if row is None:
            raise RuntimeError("INSERT into _sqlcharacteraction returned no row")
        return row[0]

    def update(self, character_name: str, index: int, template: str) -> None:
        actions = self.get_all_for_character(character_name)
        if not 1 <= index <= len(actions):
            raise IndexError(f"Action index {index} out of range (1-{len(actions)})")
        self._db.execute(
            "UPDATE _sqlcharacteraction SET template=? WHERE character_name=? AND position=?",
            (template, character_name, index - 1),
        )

    def remove(self, character_name: str, index: int) -> None:
        actions = self.get_all_for_character(character_name)
        if not 1 <= index <= len(actions):
            raise IndexError(f"Action index {index} out of range (1-{len(actions)})")
        pos = index - 1
        self._db.execute(
            "DELETE FROM _sqlcharacteraction WHERE character_name=? AND position=?",
            (character_name, pos),
        )
        self._db.execute(
            "UPDATE _sqlcharacteraction SET position=position-1 WHERE character_name=? AND position>?",
            (character_name, pos),
        )

    def remove_all_for_character(self, character_name: str) -> None:
        self._db.execute(
            "DELETE FROM _sqlcharacteraction WHERE character_name=?",
            (character_name,),
        )

    def rename_character(self, old_name: str, new_name: str) -> None:
        self._db.execute(
            "UPDATE _sqlcharacteraction SET character_name=? WHERE character_name=?",
            (new_name, old_name),
        )


class _SqlWebLoginTokenState(WebLoginTokenState):
    def __init__(self, db: sqlite3.Connection) -> None:
        self._db = db

    def create(self, discord_id: int) -> str:
        token = secrets.token_urlsafe(32)
        now = int(time.time())
        self._db.execute(
            "INSERT INTO _sqlweblogintoken (token, discord_id, expires_at, used) VALUES (?, ?, ?, 0)",
            (token, discord_id, now + _WEB_LOGIN_TOKEN_TTL),
        )
        return token

    def find_valid(self, token: str) -> int | None:
        now = int(time.time())
        row = self._db.execute(
            "SELECT discord_id FROM _sqlweblogintoken WHERE token=? AND used=0 AND expires_at>?",
            (token, now),
        ).fetchone()
        return row[0] if row is not None else None

    def mark_used(self, token: str) -> None:
        self._db.execute(
            "UPDATE _sqlweblogintoken SET used=1 WHERE token=?",
            (token,),
        )

    def prune_expired(self) -> None:
        now = int(time.time())
        self._db.execute(
            "DELETE FROM _sqlweblogintoken WHERE expires_at<=?",
            (now,),
        )


class _SqlSessionSecretState(SessionSecretState):
    def __init__(self, db: sqlite3.Connection) -> None:
        self._db = db

    def _load(self) -> tuple[str, int] | None:
        row = self._db.execute(
            "SELECT secret, expires_at FROM _sqlsessionsecret WHERE id=1"
        ).fetchone()
        return (str(row[0]), int(row[1])) if row is not None else None

    def _store(self, secret: str, expires_at: int) -> None:
        self._db.execute(
            "INSERT INTO _sqlsessionsecret (id, secret, expires_at) VALUES (1, ?, ?)"
            " ON CONFLICT(id) DO UPDATE SET secret=excluded.secret, expires_at=excluded.expires_at",
            (secret, expires_at),
        )


class SqlState(State):
    def __init__(self, source: str) -> None:
        state_type, state_source = source.split(":", maxsplit=1)
        if state_type != "sqlite":
            raise ValueError(f"Unsupported state type: {state_type}")

        path = Path(state_source)
        check_state_directory(source, path.parent)

        self._db = sqlite3.connect(
            path,
            check_same_thread=False,
            isolation_level=None,  # autocommit
        )
        self._db.execute("PRAGMA journal_mode=WAL;")
        self._db.execute("PRAGMA synchronous=NORMAL;")

        for statement in _CREATE_TABLES.strip().split(";"):
            statement = statement.strip()
            if statement:
                self._db.execute(statement)

        self._migrate(self._db)

        self._characters = _SqlCharacterState(self._db)
        self._players = _SqlPlayerState(self._db)
        self._web_login_tokens = _SqlWebLoginTokenState(self._db)
        self._character_actions = _SqlCharacterActionState(self._db)
        self._session_secret = _SqlSessionSecretState(self._db)

    @staticmethod
    def _migrate(db: sqlite3.Connection) -> None:
        """Apply schema migrations for databases created by older versions."""
        cursor = db.execute("PRAGMA table_info(_sqlcharacterdata);")
        columns = [row[1] for row in cursor.fetchall()]

        obsolete = {
            "active",
            "level",
            "strength",
            "agility",
            "stamina",
            "personality",
            "intelligence",
            "luck",
            "initial_luck",
            "hit_points",
            "equipment",
            "occupation",
            "exp",
            "alignment",
            "initiative_modifier",
            "initiative_time",
            "hit_die",
            "augur",
            "cls",
            "creation_time",
            "user",
        }
        needs_rebuild = bool(obsolete & set(columns))

        if "initiative_dice" not in columns:
            db.execute(
                "ALTER TABLE _sqlcharacterdata ADD COLUMN initiative_dice TEXT DEFAULT NULL;"
            )
        if "last_used" not in columns:
            db.execute(
                "ALTER TABLE _sqlcharacterdata ADD COLUMN last_used INTEGER DEFAULT NULL;"
            )
        if "player_id" not in columns:
            db.execute(
                "ALTER TABLE _sqlcharacterdata ADD COLUMN player_id INTEGER DEFAULT NULL;"
            )

        if needs_rebuild:
            db.execute("""
                CREATE TABLE _sqlcharacterdata_new (
                    name TEXT NOT NULL PRIMARY KEY,
                    player_id INTEGER,
                    initiative INTEGER,
                    initiative_dice TEXT,
                    last_used INTEGER
                );
            """)
            db.execute("""
                INSERT INTO _sqlcharacterdata_new
                    (name, player_id, initiative, initiative_dice, last_used)
                SELECT name, player_id, initiative, initiative_dice, last_used
                FROM _sqlcharacterdata;
            """)
            db.execute("DROP TABLE _sqlcharacterdata;")
            db.execute("ALTER TABLE _sqlcharacterdata_new RENAME TO _sqlcharacterdata;")

        # Assign a grace-period last_used to rows that have none, so they
        # are not immediately eligible for pruning after this migration.
        grace_ts = int(time.time()) - CORE_CFG.prune_threshold_days * 86400 // 2
        db.execute(
            "UPDATE _sqlcharacterdata SET last_used=? WHERE last_used IS NULL;",
            (grace_ts,),
        )

    @property
    def characters(self) -> CharacterState:
        return self._characters

    @property
    def players(self) -> PlayerState:
        return self._players

    @property
    def web_login_tokens(self) -> WebLoginTokenState:
        return self._web_login_tokens

    @property
    def character_actions(self) -> CharacterActionState:
        return self._character_actions

    @property
    def session_secret(self) -> SessionSecretState:
        return self._session_secret
