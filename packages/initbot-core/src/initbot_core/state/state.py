# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import secrets
import time
from abc import ABC, abstractmethod
from collections.abc import Iterable, Sequence, Set
from typing import Final

from initbot_core.data.character import CharacterData, NewCharacterData
from initbot_core.data.player import PlayerData
from initbot_core.utils import (
    get_exact_or_unique_prefix_match,
    normalize_str,
)


class PartialState:
    """Marker base class for all partial state objects.

    Serves as the common base for CharacterState and PlayerState so that
    State.import_from can discover sub-state attributes via issubclass checks
    at runtime.
    """


class CharacterState(PartialState, ABC):
    @abstractmethod
    def get_all(self) -> Sequence[CharacterData]:
        raise NotImplementedError()

    def get_from_tokens(
        self,
        tokens: Iterable[str],
        create: bool = False,
        player_id: int | None = None,
    ) -> CharacterData:
        return self.get_from_str(" ".join(tokens), create, player_id)

    def get_from_str(
        self,
        name: str,
        create: bool = False,
        player_id: int | None = None,
    ) -> CharacterData:
        if name:
            return self.get_from_name(name, create, player_id)
        if player_id is not None:
            return self.get_from_player_id(player_id)
        raise KeyError("No character name or player_id provided")

    def get_from_player_id(self, player_id: int) -> CharacterData:
        """Find the unique character owned by the given player."""
        chars = [cdi for cdi in self.get_all() if cdi.player_id == player_id]
        if len(chars) == 1:
            return chars[0]
        raise KeyError(
            f"Expected one character for player_id={player_id}, found {len(chars)}"
        )

    def get_from_name(
        self,
        name: str,
        create: bool = False,
        player_id: int | None = None,
    ) -> CharacterData:
        try:
            return get_exact_or_unique_prefix_match(
                name, self.get_all(), lambda cdi: cdi.name
            )
        except KeyError as err:
            if create and player_id is not None:
                return self.add_store_and_get(
                    NewCharacterData(name=name, player_id=player_id)
                )
            raise KeyError(f"Unable to find character with name '{name}'") from err

    def add_store_and_get(self, char_data: NewCharacterData) -> CharacterData:
        normalized = normalize_str(char_data.name)
        for existing in self.get_all():
            if normalize_str(existing.name) == normalized:
                raise ValueError(
                    f"A character named '{existing.name}' already exists "
                    f"(character names must be unique ignoring case)"
                )
        return self._add_store_and_get(char_data)

    def rename_and_store(
        self, char_data: CharacterData, new_name: str
    ) -> CharacterData:
        normalized = normalize_str(new_name)
        for existing in self.get_all():
            if normalize_str(existing.name) == normalized:
                raise ValueError(
                    f"A character named '{existing.name}' already exists "
                    f"(character names must be unique ignoring case)"
                )
        return self._rename_and_store(char_data, new_name)

    @abstractmethod
    def _add_store_and_get(self, char_data: NewCharacterData) -> CharacterData:
        raise NotImplementedError()

    @abstractmethod
    def _rename_and_store(
        self, char_data: CharacterData, new_name: str
    ) -> CharacterData:
        raise NotImplementedError()

    @abstractmethod
    def remove_and_store(self, char_data: CharacterData) -> None:
        raise NotImplementedError()

    @abstractmethod
    def update_and_store(self, char_data: CharacterData) -> None:
        raise NotImplementedError()

    @abstractmethod
    def import_from(self, src: "CharacterState") -> None:
        raise NotImplementedError()


class PlayerState(PartialState, ABC):
    @abstractmethod
    def upsert(self, discord_id: int, name: str) -> PlayerData:
        raise NotImplementedError()

    @abstractmethod
    def get_from_id(self, player_id: int) -> PlayerData:
        """Look up by internal player ID (used as foreign key by other entities)."""
        raise NotImplementedError()

    @abstractmethod
    def get_from_discord_id(self, discord_id: int) -> PlayerData | None:
        """Look up by Discord snowflake ID."""
        raise NotImplementedError()

    @abstractmethod
    def get_all(self) -> Sequence[PlayerData]:
        raise NotImplementedError()

    @abstractmethod
    def import_from(self, src: "PlayerState") -> None:
        raise NotImplementedError()


class WebLoginTokenState(ABC):
    """Stores short-lived, single-use tokens that authenticate a player via the web app."""

    @abstractmethod
    def create(self, discord_id: int) -> str:
        """Generate a token for the given Discord user ID, persist it, and return it."""
        raise NotImplementedError()

    @abstractmethod
    def find_valid(self, token: str) -> int | None:
        """Return the discord_id for a token that exists, has not been used, and has not expired.

        Returns None if the token is unknown, already used, or expired.
        """
        raise NotImplementedError()

    @abstractmethod
    def mark_used(self, token: str) -> None:
        """Invalidate a token after a successful login (single-use enforcement)."""
        raise NotImplementedError()

    @abstractmethod
    def prune_expired(self) -> None:
        """Delete tokens whose expiry timestamp is in the past."""
        raise NotImplementedError()


class CharacterActionState(PartialState, ABC):
    """Stores ordered action templates for each character."""

    @abstractmethod
    def get_all_for_character(self, character_name: str) -> Sequence[str]:
        """Return all action templates for the given character, in insertion order."""
        raise NotImplementedError()

    @abstractmethod
    def add(self, character_name: str, template: str) -> int:
        """Append a template and return its 1-based index."""
        raise NotImplementedError()

    @abstractmethod
    def update(self, character_name: str, index: int, template: str) -> None:
        """Replace the template at 1-based index. Raises IndexError if out of range."""
        raise NotImplementedError()

    @abstractmethod
    def remove(self, character_name: str, index: int) -> None:
        """Delete the template at 1-based index. Raises IndexError if out of range.

        Remaining actions renumber to fill the gap.
        """
        raise NotImplementedError()

    @abstractmethod
    def remove_all_for_character(self, character_name: str) -> None:
        """Delete every action belonging to the given character."""
        raise NotImplementedError()

    @abstractmethod
    def rename_character(self, old_name: str, new_name: str) -> None:
        """Update the character_name key for all actions belonging to old_name."""
        raise NotImplementedError()

    @abstractmethod
    def import_from(self, src: "CharacterActionState") -> None:
        raise NotImplementedError()


_SESSION_SECRET_TTL: Final[int] = (
    8 * 60 * 60
)  # 8 hours, matches SESSION_TTL in initbot-web


class SessionSecretState(ABC):
    """Stores the persistent session-signing secret used by the web app."""

    @abstractmethod
    def _load(self) -> tuple[str, int] | None:
        """Return (secret, expires_at) if a record exists, else None."""
        raise NotImplementedError()

    @abstractmethod
    def _store(self, secret: str, expires_at: int) -> None:
        """Persist secret and expiry, replacing any existing record."""
        raise NotImplementedError()

    def get_or_rotate(self) -> str:
        """Return the current secret, generating a new one if absent or expired."""
        now = int(time.time())
        entry = self._load()
        if entry is not None and entry[1] > now:
            return entry[0]
        new_secret = secrets.token_urlsafe(32)
        self._store(new_secret, now + _SESSION_SECRET_TTL)
        return new_secret


class State(ABC):
    @property
    @abstractmethod
    def characters(self) -> CharacterState:
        raise NotImplementedError()

    @property
    @abstractmethod
    def players(self) -> PlayerState:
        raise NotImplementedError()

    @property
    @abstractmethod
    def web_login_tokens(self) -> WebLoginTokenState:
        raise NotImplementedError()

    @property
    @abstractmethod
    def character_actions(self) -> CharacterActionState:
        raise NotImplementedError()

    @property
    @abstractmethod
    def session_secret(self) -> SessionSecretState:
        raise NotImplementedError()

    def import_from(self, src: "State") -> None:
        target_attributes = {
            name: getattr(self, name) for name in dir(self) if not name.startswith("_")
        }
        target_states = {
            name: value
            for name, value in target_attributes.items()
            if issubclass(type(value), PartialState)
        }
        for target_state_name, target_state in target_states.items():
            print(f"Importing {target_state_name} from {src}")
            target_state.import_from(getattr(src, target_state_name))

    @classmethod
    @abstractmethod
    def get_supported_state_types(cls) -> Set[str]:
        raise NotImplementedError()
