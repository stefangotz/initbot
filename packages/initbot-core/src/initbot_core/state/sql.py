# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import dataclasses
import secrets
import time
from collections.abc import Iterable, Mapping, Sequence, Set
from dataclasses import asdict
from inspect import isclass
from pathlib import Path
from typing import Any, cast

from peewee import (
    AutoField,
    BooleanField,
    CharField,
    IntegerField,
    Model,
    SqliteDatabase,
)

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


class _SqlCharacterData(Model):
    name = CharField(unique=True, primary_key=True)
    initiative = IntegerField(null=True)
    initiative_dice = CharField(null=True)
    last_used = IntegerField(null=True)
    player_id = IntegerField(null=True)


class _SqlCharacterState(CharacterState):
    def get_all(self) -> Sequence[CharacterData]:
        return tuple(_SqlCharacterData.select())

    def _add_store_and_get(self, char_data: NewCharacterData) -> CharacterData:
        if char_data.last_used is None:
            char_data.last_used = int(time.time())
        return _SqlCharacterData.create(  # type: ignore[return-value]
            **{k: v for k, v in asdict(char_data).items() if v is not None}
        )

    def remove_and_store(self, char_data: CharacterData) -> None:
        _SqlCharacterData.delete().where(
            _SqlCharacterData.name == char_data.name
        ).execute()

    def _rename_and_store(
        self, char_data: CharacterData, new_name: str
    ) -> CharacterData:
        _SqlCharacterData.update(name=new_name).where(
            _SqlCharacterData.name == char_data.name
        ).execute()
        return _SqlCharacterData.get(_SqlCharacterData.name == new_name)  # type: ignore[return-value]

    def update_and_store(self, char_data: CharacterData) -> None:
        if not isinstance(char_data, _SqlCharacterData):
            raise TypeError(
                f"Only character data returned by the State class can be updated: {char_data}"
            )
        # pylint: disable-next=protected-access
        meta = type(char_data)._meta
        pk_name = meta.primary_key.name
        fields_to_update = {
            field: char_data.__data__.get(name)
            for name, field in meta.fields.items()
            if name != pk_name
        }
        _SqlCharacterData.update(fields_to_update).where(
            _SqlCharacterData.name == char_data.name
        ).execute()

    def import_from(self, src: CharacterState) -> None:
        for cdi in src.get_all():
            _SqlCharacterData.create(**{
                k: v
                for k, v in (
                    (f.name, getattr(cdi, f.name, None))
                    for f in dataclasses.fields(NewCharacterData)
                )
                if v is not None
            })


class _SqlPlayerData(Model):
    id = AutoField()  # internal primary key, auto-increment
    discord_id = IntegerField(null=True, unique=True)
    name = CharField()


class _SqlPlayerState(PlayerState):
    def upsert(self, discord_id: int, name: str) -> PlayerData:
        player = _SqlPlayerData.get_or_none(_SqlPlayerData.discord_id == discord_id)
        if player is not None:
            if player.name != name:
                _SqlPlayerData.update(name=name).where(
                    _SqlPlayerData.id == player.id
                ).execute()
                player.name = name
            return player
        return _SqlPlayerData.create(discord_id=discord_id, name=name)  # type: ignore[return-value]

    def get_from_id(self, player_id: int) -> PlayerData:
        result = _SqlPlayerData.get_or_none(_SqlPlayerData.id == player_id)
        if result is None:
            raise KeyError(f"No player with id={player_id}")
        return result

    def get_from_discord_id(self, discord_id: int) -> PlayerData | None:
        result = _SqlPlayerData.get_or_none(_SqlPlayerData.discord_id == discord_id)
        return result

    def get_all(self) -> Sequence[PlayerData]:
        return tuple(_SqlPlayerData.select())

    def import_from(self, src: PlayerState) -> None:
        for p in src.get_all():
            _SqlPlayerData.create(id=p.id, discord_id=p.discord_id, name=p.name)


class _SqlCharacterAction(Model):
    # No foreign-key constraint on character_name: SQLite FK enforcement requires
    # PRAGMA foreign_keys=ON per connection, which Peewee does not set by default,
    # and adding it now would risk breaking existing deployments.
    #
    # Referential integrity is maintained at the command layer instead:
    # initbot_chat.commands.character calls remove_all_for_character() before
    # deleting a character. CharacterState.remove_and_store() does NOT cascade;
    # any code that removes characters outside the command layer must call
    # remove_all_for_character() explicitly to avoid leaving orphaned rows.
    id = AutoField()
    character_name = CharField()
    position = IntegerField()  # 0-based; kept contiguous after removes
    template = CharField()


class _SqlCharacterActionState(CharacterActionState):
    def get_all_for_character(self, character_name: str) -> Sequence[str]:
        rows = (
            _SqlCharacterAction
            .select()
            .where(_SqlCharacterAction.character_name == character_name)
            .order_by(_SqlCharacterAction.position)
        )
        return [row.template for row in rows]

    def add(self, character_name: str, template: str) -> int:
        next_pos = len(self.get_all_for_character(character_name))
        _SqlCharacterAction.create(
            character_name=character_name,
            position=next_pos,
            template=template,
        )
        return next_pos + 1

    def update(self, character_name: str, index: int, template: str) -> None:
        actions = self.get_all_for_character(character_name)
        if not 1 <= index <= len(actions):
            raise IndexError(f"Action index {index} out of range (1-{len(actions)})")
        _SqlCharacterAction.update(template=template).where(
            (_SqlCharacterAction.character_name == character_name)
            & (_SqlCharacterAction.position == index - 1)
        ).execute()

    def remove(self, character_name: str, index: int) -> None:
        actions = self.get_all_for_character(character_name)
        if not 1 <= index <= len(actions):
            raise IndexError(f"Action index {index} out of range (1-{len(actions)})")
        pos = index - 1
        _SqlCharacterAction.delete().where(
            (_SqlCharacterAction.character_name == character_name)
            & (_SqlCharacterAction.position == pos)
        ).execute()
        # Renumber remaining rows to keep positions contiguous
        _SqlCharacterAction.update(position=_SqlCharacterAction.position - 1).where(
            (_SqlCharacterAction.character_name == character_name)
            & (_SqlCharacterAction.position > pos)
        ).execute()

    def remove_all_for_character(self, character_name: str) -> None:
        _SqlCharacterAction.delete().where(
            _SqlCharacterAction.character_name == character_name
        ).execute()

    def rename_character(self, old_name: str, new_name: str) -> None:
        _SqlCharacterAction.update(character_name=new_name).where(
            _SqlCharacterAction.character_name == old_name
        ).execute()

    def import_from(self, src: CharacterActionState) -> None:
        for cdi in _SqlCharacterData.select():
            for pos, template in enumerate(src.get_all_for_character(cdi.name)):
                _SqlCharacterAction.create(
                    character_name=cdi.name,
                    position=pos,
                    template=template,
                )


class _SqlWebLoginToken(Model):
    token = CharField(primary_key=True)
    discord_id = IntegerField()
    expires_at = IntegerField()
    used = BooleanField(default=False)


class _SqlWebLoginTokenState(WebLoginTokenState):
    def create(self, discord_id: int) -> str:
        token = secrets.token_urlsafe(32)
        now = int(time.time())
        _SqlWebLoginToken.create(
            token=token,
            discord_id=discord_id,
            expires_at=now + _WEB_LOGIN_TOKEN_TTL,
        )
        return token

    def find_valid(self, token: str) -> int | None:
        now = int(time.time())
        row = _SqlWebLoginToken.get_or_none(
            (_SqlWebLoginToken.token == token)
            & ~_SqlWebLoginToken.used
            & (_SqlWebLoginToken.expires_at > now)
        )
        return row.discord_id if row is not None else None

    def mark_used(self, token: str) -> None:
        _SqlWebLoginToken.update(used=True).where(
            _SqlWebLoginToken.token == token
        ).execute()

    def prune_expired(self) -> None:
        now = int(time.time())
        _SqlWebLoginToken.delete().where(_SqlWebLoginToken.expires_at <= now).execute()


class _SqlSessionSecret(Model):
    id = IntegerField(primary_key=True)  # single-row table; always id=1
    secret = CharField()
    expires_at = IntegerField()


class _SqlSessionSecretState(SessionSecretState):
    def _load(self) -> tuple[str, int] | None:
        row = _SqlSessionSecret.get_or_none(_SqlSessionSecret.id == 1)
        return (str(row.secret), int(row.expires_at)) if row is not None else None

    def _store(self, secret: str, expires_at: int) -> None:
        _SqlSessionSecret.insert(
            id=1, secret=secret, expires_at=expires_at
        ).on_conflict_replace().execute()


class SqlState(State):
    def __init__(
        self,
        source: str,
    ) -> None:
        self._characters = _SqlCharacterState()
        self._players = _SqlPlayerState()
        self._web_login_tokens = _SqlWebLoginTokenState()
        self._character_actions = _SqlCharacterActionState()
        self._session_secret = _SqlSessionSecretState()

        state_type, state_source = source.split(":", maxsplit=1)
        if state_type == "sqlite":
            path = Path(state_source)
            check_state_directory(source, path.parent)
            if not path.exists():
                path.touch(exist_ok=True)
            self._db = SqliteDatabase(
                path,
                pragmas={"journal_mode": "wal", "synchronous": "normal"},
            )

        else:
            raise ValueError(f"Unsupported state type: {state_type}")

        data_classes = _get_data_classes()
        self._db.bind(data_classes)
        self._db.create_tables(data_classes, safe=True)

        self._migrate(self._db)

    @staticmethod
    def _migrate(db: SqliteDatabase) -> None:
        """Apply schema migrations."""
        with db.connection_context():
            # --- _sqlcharacterdata ---
            cursor = db.execute_sql("PRAGMA table_info(_sqlcharacterdata);")
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
                # legacy names from even older migrations
                "creation_time",
                "user",
            }
            needs_rebuild = bool(obsolete & set(columns))

            if "initiative_dice" not in columns:
                db.execute_sql(
                    "ALTER TABLE _sqlcharacterdata ADD COLUMN initiative_dice TEXT DEFAULT NULL;"
                )
            if "last_used" not in columns:
                db.execute_sql(
                    "ALTER TABLE _sqlcharacterdata ADD COLUMN last_used INTEGER DEFAULT NULL;"
                )
            if "player_id" not in columns:
                db.execute_sql(
                    "ALTER TABLE _sqlcharacterdata ADD COLUMN player_id INTEGER DEFAULT NULL;"
                )

            if needs_rebuild:
                db.execute_sql("""
                    CREATE TABLE _sqlcharacterdata_new (
                        name TEXT NOT NULL PRIMARY KEY,
                        initiative INTEGER,
                        initiative_dice TEXT,
                        last_used INTEGER,
                        player_id INTEGER
                    );
                """)
                db.execute_sql("""
                    INSERT INTO _sqlcharacterdata_new
                        (name, initiative, initiative_dice, last_used, player_id)
                    SELECT name, initiative, initiative_dice, last_used, player_id
                    FROM _sqlcharacterdata;
                """)
                db.execute_sql("DROP TABLE _sqlcharacterdata;")
                db.execute_sql(
                    "ALTER TABLE _sqlcharacterdata_new RENAME TO _sqlcharacterdata;"
                )

            # Assign a grace-period last_used to rows that have none, so they
            # are not immediately eligible for pruning after this migration.
            grace_ts = int(time.time()) - CORE_CFG.prune_threshold_days * 86400 // 2
            db.execute_sql(
                "UPDATE _sqlcharacterdata SET last_used = ? WHERE last_used IS NULL;",
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

    @classmethod
    def get_supported_state_types(cls) -> Set[str]:
        return {"sqlite"}


def _import_from(cls: type[Any], dicts: Iterable[Mapping[str, Any]]) -> None:
    cls.insert_many(dicts).execute()


def _get_data_classes() -> Sequence[type[Model]]:
    return tuple(
        cast(type[Model], i)
        for i in globals().values()
        if isclass(i) and issubclass(i, Model) and i is not Model
    )
