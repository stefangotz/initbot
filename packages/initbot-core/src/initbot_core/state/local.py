# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
import time
from collections.abc import Mapping, MutableSequence, Sequence, Set
from dataclasses import asdict
from pathlib import Path
from typing import Any, Final

from pydantic import BaseModel

from initbot_core.config import CORE_CFG
from initbot_core.data.character import CharacterData, NewCharacterData
from initbot_core.data.player import PlayerData
from initbot_core.state.state import (
    CharacterActionState,
    CharacterState,
    PlayerState,
    SessionSecretState,
    State,
    WebLoginTokenState,
)
from initbot_core.state.validation import check_state_directory


class LocalBaseModel(BaseModel):
    def as_dict(self) -> Mapping[str, Any]:
        return self.model_dump()


class LocalCharacterData(LocalBaseModel):
    name: str
    player_id: int
    initiative: int | None = None
    initiative_dice: str | None = None
    last_used: int | None = None
    actions: list[str] = []


class LocalCharactersData(LocalBaseModel):
    characters: MutableSequence[LocalCharacterData] = []


class LocalCharacterState(CharacterState):
    def __init__(self, source_dir: Path) -> None:
        chars_data = LocalCharactersData()
        self._path: Final[Path] = source_dir / "characters.json"
        if self._path.exists():
            with self._path.open() as file_desc:
                chars_data = LocalCharactersData.model_validate_json(file_desc.read())
        else:
            logging.info("No character data loaded from %s", self._path)

        self._characters: MutableSequence[LocalCharacterData] = chars_data.characters

        # Assign a grace-period last_used to characters that have none, so they
        # are not immediately eligible for pruning after this migration.
        grace_ts = int(time.time()) - CORE_CFG.prune_threshold_days * 86400 // 2
        migrated = False
        for char in self._characters:
            if char.last_used is None:
                char.last_used = grace_ts
                migrated = True
        if migrated:
            self._store()

    def get_all(self) -> Sequence[CharacterData]:
        return self._characters

    def _add_store_and_get(self, char_data: NewCharacterData) -> CharacterData:
        local_char_data = LocalCharacterData(**asdict(char_data))
        if local_char_data.last_used is None:
            local_char_data.last_used = int(time.time())
        self._characters.append(local_char_data)
        self._store()
        return local_char_data

    def remove_and_store(self, char_data: CharacterData) -> None:
        if not isinstance(char_data, LocalCharacterData):
            raise TypeError(
                f"Only character data returned by the State class can be removed: {char_data}"
            )
        self._characters.remove(char_data)
        self._store()

    def _rename_and_store(
        self, char_data: CharacterData, new_name: str
    ) -> CharacterData:
        if not isinstance(char_data, LocalCharacterData):
            raise TypeError(
                f"Only character data returned by the State class can be renamed: {char_data}"
            )
        char_data.name = new_name
        self._store()
        return char_data

    def update_and_store(self, char_data: CharacterData) -> None:
        if not isinstance(char_data, LocalCharacterData):
            raise TypeError(
                f"Only character data returned by the State class can be updated: {char_data}"
            )
        if char_data not in self._characters:
            raise ValueError(
                f"Character data is not present in the data store yet; this is not supported: {char_data}"
            )
        self._store()

    def _store(self) -> None:
        with open(self._path, "w", encoding="UTF8") as file_desc:
            file_desc.write(
                LocalCharactersData(characters=self._characters).model_dump_json()
            )

    def import_from(self, src: CharacterState) -> None:
        raise NotImplementedError()


class LocalCharacterActionState(CharacterActionState):
    # Actions are stored as an embedded list on LocalCharacterData, so they are
    # serialised and deleted together with the character — structural integrity
    # is guaranteed by the JSON file format.
    #
    # Cascade on character deletion is handled at the command layer
    # (initbot_chat.commands.character) rather than here. CharacterState
    # .remove_and_store() does NOT call remove_all_for_character; callers that
    # bypass the command layer must do so explicitly.
    def __init__(self, character_state: LocalCharacterState) -> None:
        self._character_state = character_state

    def _find(self, character_name: str) -> LocalCharacterData:
        for char in self._character_state.get_all():
            if char.name == character_name and isinstance(char, LocalCharacterData):
                return char
        raise KeyError(f"Character '{character_name}' not found")

    def get_all_for_character(self, character_name: str) -> Sequence[str]:
        return list(self._find(character_name).actions)

    def add(self, character_name: str, template: str) -> int:
        char = self._find(character_name)
        char.actions.append(template)
        self._character_state.update_and_store(char)
        return len(char.actions)

    def update(self, character_name: str, index: int, template: str) -> None:
        char = self._find(character_name)
        if not 1 <= index <= len(char.actions):
            raise IndexError(
                f"Action index {index} out of range (1-{len(char.actions)})"
            )
        char.actions[index - 1] = template
        self._character_state.update_and_store(char)

    def remove(self, character_name: str, index: int) -> None:
        char = self._find(character_name)
        if not 1 <= index <= len(char.actions):
            raise IndexError(
                f"Action index {index} out of range (1-{len(char.actions)})"
            )
        del char.actions[index - 1]
        self._character_state.update_and_store(char)

    def remove_all_for_character(self, character_name: str) -> None:
        try:
            char = self._find(character_name)
            char.actions.clear()
            self._character_state.update_and_store(char)
        except KeyError:
            pass

    def rename_character(self, old_name: str, new_name: str) -> None:
        pass  # Actions are embedded in LocalCharacterData; renaming the character handles this

    def import_from(self, src: CharacterActionState) -> None:
        raise NotImplementedError()


class LocalPlayerData(LocalBaseModel):
    id: int
    discord_id: int
    name: str


class LocalPlayersData(LocalBaseModel):
    players: MutableSequence[LocalPlayerData] = []


class LocalPlayerState(PlayerState):
    def __init__(self, source_dir: Path) -> None:
        players_data = LocalPlayersData()
        self._path: Final[Path] = source_dir / "players.json"
        if self._path.exists():
            with self._path.open() as file_desc:
                players_data = LocalPlayersData.model_validate_json(file_desc.read())
        else:
            logging.info("No player data loaded from %s", self._path)
        self._players: MutableSequence[LocalPlayerData] = players_data.players

    def _next_id(self) -> int:
        return max((p.id for p in self._players), default=0) + 1

    def upsert(self, discord_id: int, name: str) -> PlayerData:
        for player in self._players:
            if player.discord_id == discord_id:
                player.name = name
                self._store()
                return player
        new_player = LocalPlayerData(
            id=self._next_id(), discord_id=discord_id, name=name
        )
        self._players.append(new_player)
        self._store()
        return new_player

    def get_from_id(self, player_id: int) -> PlayerData:
        for player in self._players:
            if player.id == player_id:
                return player
        raise KeyError(f"No player with id={player_id}")

    def get_from_discord_id(self, discord_id: int) -> PlayerData | None:
        for player in self._players:
            if player.discord_id == discord_id:
                return player
        return None

    def get_all(self) -> Sequence[PlayerData]:
        return self._players

    def _store(self) -> None:
        with open(self._path, "w", encoding="UTF8") as file_desc:
            file_desc.write(LocalPlayersData(players=self._players).model_dump_json())

    def import_from(self, src: PlayerState) -> None:
        raise NotImplementedError()


class _LocalWebLoginTokenState(WebLoginTokenState):
    def create(self, discord_id: int) -> str:
        raise NotImplementedError("Web login tokens require SQLite state")

    def find_valid(self, token: str) -> int | None:
        raise NotImplementedError("Web login tokens require SQLite state")

    def mark_used(self, token: str) -> None:
        raise NotImplementedError("Web login tokens require SQLite state")

    def prune_expired(self) -> None:
        raise NotImplementedError("Web login tokens require SQLite state")


class _LocalSessionSecretState(SessionSecretState):
    def _load(self) -> tuple[str, int] | None:
        raise NotImplementedError("Session secrets require SQLite state")

    def _store(self, secret: str, expires_at: int) -> None:
        raise NotImplementedError("Session secrets require SQLite state")


class LocalState(State):
    def __init__(self, source: str) -> None:
        source_dir = Path(source.split(":", maxsplit=1)[-1])
        check_state_directory(source, source_dir)
        self._players = LocalPlayerState(source_dir)
        self._characters = LocalCharacterState(source_dir)
        self._web_login_tokens = _LocalWebLoginTokenState()
        self._character_actions = LocalCharacterActionState(self._characters)
        self._session_secret = _LocalSessionSecretState()

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
        return {"json"}
