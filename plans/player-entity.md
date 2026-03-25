# Plan: Introduce PlayerData entity

## Context

The pruning notification task calls `guild.get_member_named(username)` using the `user: str`
field on `CharacterData`, which stores a Discord display name. This fails when the display
name changes, the user left the server, or the bot lacks the `GUILD_MEMBERS` privileged
intent. The reliable fix is to use `guild.get_member(discord_id)` with a Discord snowflake
ID instead.

The display name is still valuable — character listings show `**Harold** (_alice_)` so
players know who owns what. Storing both ID and name redundantly on every `CharacterData`
row would work but is structurally wrong: if a player has five characters, their name is
stored five times with no single update point.

The right fix is a `PlayerData` entity: one record per Discord user, holding an internal
primary key (`id`), the Discord snowflake (`discord_id`), and the current display name.
Characters reference it by the internal `id` — not by `discord_id` — so the data model
has no structural dependency on Discord. The display name is refreshed on every command
invocation, so it stays current without any explicit sync step.

---

## Stage 1 — `PlayerData` entity and `PlayerState` (core only)

- [x] Complete

**Goal:** Introduce the new entity and its storage layer. No behaviour change anywhere else.

### New files / changes

**`data/player.py`** — new file
```python
@dataclass
class PlayerData(BaseData):
    id: int  # Internal primary key, auto-assigned; used as FK by other entities
    discord_id: int  # Discord snowflake, unique but not the primary key
    name: str  # Display name, refreshed on each command invocation
```

**`state/state.py`**
Add abstract `PlayerState`:
- `upsert(discord_id: int, name: str) -> PlayerData`
- `get_from_id(player_id: int) -> PlayerData | None` — look up by internal ID
- `get_from_discord_id(discord_id: int) -> PlayerData | None` — look up by Discord snowflake
- `get_all() -> Sequence[PlayerData]`

Add `players: PlayerState` property to `State`.

**`state/local.py`**
Implement `PlayerState` backed by `players.json`. Upsert by `discord_id`; auto-increment
`id` from the current max.

**`state/sql.py`**
Add `_SqlPlayerData` Peewee model (`id` AutoField primary key, `discord_id` unique integer,
`name` text). Implement `PlayerState` against that table.

### Tests
- `test_player_upsert_creates_record`
- `test_player_upsert_updates_name_on_second_call`
- `test_player_upsert_assigns_unique_ids`
- `test_player_get_from_id_returns_record`
- `test_player_get_from_id_returns_none_when_missing`
- `test_player_get_from_discord_id_returns_record`
- `test_player_get_from_discord_id_returns_none_when_missing`
- Run against both JSON and SQL backends via the existing fixture pattern.

### Validation
`pytest -q` passes. No changes to chat layer or existing character behaviour.

---

## Stage 2 — Add `player_id` to `CharacterData`

- [x] Complete

**Goal:** Extend the character schema with a nullable foreign key. No backfill yet.

### Changes

**`data/character.py`**
```python
player_id: int | None = None
```
Keep `user: str` untouched.

**`state/local.py`** — no migration needed; JSON deserialisation defaults missing key to `None`.

**`state/sql.py`**
Add `player_id = IntegerField(null=True)` to `_SqlCharacterData`.
Add migration: `ALTER TABLE _sqlcharacterdata ADD COLUMN player_id INTEGER` (guarded by
column-existence check, same pattern as the existing `creation_time → last_used` migration).

### Tests
- `test_character_with_player_id_round_trips_json`
- `test_character_with_player_id_round_trips_sql`
- `test_character_without_player_id_defaults_to_none` (migration / legacy record)

### Validation
`pytest -q` passes. `player_id` is stored and retrieved but unused by any logic yet.

---

## Stage 3 — `sync_player` helper, backfill, and display update (chat layer)

- [x] Complete

**Goal:** Start populating `player_id` on characters as players use commands, and switch
character displays to show the name from `PlayerData`.

### Changes

**`commands/utils.py`** — add helper
```python
def sync_player(state: State, ctx: Context) -> PlayerData:
    """Upsert the player record and backfill player_id on their legacy characters."""
    player = state.players.upsert(discord_id=ctx.author.id, name=ctx.author.name)
    for cdi in state.characters.get_all():
        if cdi.player_id is None and cdi.user == ctx.author.name:
            cdi.player_id = player.id
            state.characters.update_and_store(cdi)
    return player
```

**`commands/character.py`** and every other command handler
Call `sync_player(state, ctx)` at the top of each command callback.

Character display (`"**Harold** (_alice_)"`) resolves the name via
`state.players.get_from_id(cdi.player_id).name` when `player_id` is set, else falls back
to `cdi.user`.

### Tests
- `test_sync_player_creates_player_record`
- `test_sync_player_backfills_player_id_on_legacy_characters`
- `test_sync_player_does_not_overwrite_existing_player_id`
- `test_character_display_uses_player_name_when_available`
- `test_character_display_falls_back_to_user_string`

### Validation
`pytest -q` passes. After running any command, the player's characters have `player_id` set.

---

## Stage 4 — Access control and pruning notification

- [x] Complete

**Goal:** Use `player_id` for ownership checks and reliable Discord member lookup.

### Changes

**`commands/character.py`** — access control
`sync_player` is called at the top of each handler and returns the current `PlayerData`.
Replace `cdi.user == ctx.author.name` with:
```python
cdi.player_id == player.id if cdi.player_id is not None else cdi.user == ctx.author.name
```

**`state/state.py`** — `get_from_user` / `get_from_tokens`
Add `get_from_player_id(player_id: int) -> CharacterData` to `CharacterState` for the
no-argument auto-select case; fall back to prefix-matching on `user` for legacy characters.

**`bot.py`** — pruning notification
Replace `guild.get_member_named(cdi.user)` with:
```python
player = state.players.get_from_id(char.player_id)
member = (
    guild.get_member(player.discord_id) if player else guild.get_member_named(cdi.user)
)
```

### Tests
- `test_access_control_uses_player_id`
- `test_access_control_falls_back_for_legacy_characters`
- `test_pruning_notification_uses_discord_id` (mock `guild.get_member`, not `get_member_named`)
- `test_pruning_notification_falls_back_for_legacy_characters`

### Validation
`pytest -q` passes. Manual: trigger pruning — notification arrives even if display name
changed since character creation.

---

## Stage 5 (cleanup) — Drop `CharacterData.user`, make `player_id` non-nullable

- [ ] Complete

**Goal:** Remove the legacy field once all characters are expected to have a `player_id`.
This stage can be deferred until the backfill has had time to run in production.

### Changes

**`data/character.py`** — remove `user: str`, change `player_id: int | None` → `player_id: int`

**`state/sql.py`** — add a startup assertion that no characters exist with `player_id IS NULL`,
or a one-time migration that assigns a sentinel player for any orphaned characters.
(SQLite does not support `DROP COLUMN` easily; the `user` column can be left in place in
the database, simply ignored by the ORM.)

**`state/local.py`** — remove handling of legacy `user` key on load.

Remove all `cdi.user` fallback branches added in earlier stages.

### Tests
Update all tests that constructed `CharacterData(user=...)` to use `player_id=...`.

### Validation
`pytest -q` passes. No references to `CharacterData.user` remain in production code.

---

## Critical files

- `packages/initbot-core/src/initbot_core/data/player.py` (new)
- `packages/initbot-core/src/initbot_core/data/character.py`
- `packages/initbot-core/src/initbot_core/state/state.py`
- `packages/initbot-core/src/initbot_core/state/local.py`
- `packages/initbot-core/src/initbot_core/state/sql.py`
- `packages/initbot-chat/src/initbot_chat/commands/utils.py`
- `packages/initbot-chat/src/initbot_chat/commands/character.py`
- `packages/initbot-chat/src/initbot_chat/bot.py`

## Reuse

- `BaseData` (`initbot_core/base.py`) — `PlayerData` extends this
- `update_and_store` on `CharacterState` — used in backfill loop
- Existing SQL migration guard pattern in `state/sql.py` — reuse for `ALTER TABLE`
- `get_unique_prefix_match` (`initbot_core/utils.py`) — not needed for PlayerState (lookup by exact ID)
