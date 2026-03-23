# Character Pruning Feature

## Context

Players frequently create short-lived characters and forget to delete them, causing data stores to accumulate stale records. This feature introduces a `last_used` timestamp on characters (repurposed from the currently-unused `creation_time` field), commands for listing/pruning/refreshing eligible characters, and a monthly notification task that proactively reminds players about their unused characters.

---

## Stage 1: Rename `creation_time` → `last_used` and auto-update on writes

**Goal:** Repurpose the existing timestamp field as the pruning criterion, keep it current on every character update, and migrate existing records with a grace-period timestamp.

### Files to modify

**`packages/initbot-core/src/initbot_core/data/character.py`**

- Rename `creation_time: int | None = None` → `last_used: int | None = None`

**`packages/initbot-core/src/initbot_core/models/character.py`**

- Rename the `creation_time` property → `last_used`

**`packages/initbot-core/src/initbot_core/state/local.py`**

- In `LocalCharacterData`: rename `creation_time` → `last_used`
- In `add_store_and_get()`: set `local_char_data.last_used = int(time.time())`
- In `update_and_store()`: set `char_data.last_used = int(time.time())` before calling `self._store()`
- In `LocalCharacterState.__init__()`: after loading `self._characters`, run a one-time migration for records with `last_used is None` — set them to `int(time.time()) - CORE_CFG.prune_threshold_days * 86400 // 2`, then call `self._store()` once if any records were updated. (Import `CORE_CFG` from `initbot_core.config`, created in Stage 2.)

**`packages/initbot-core/src/initbot_core/state/sql.py`**

- In `_SqlCharacterData`: rename `creation_time = IntegerField(null=True)` → `last_used = IntegerField(null=True)`
- In `add_store_and_get()`: set `char_data.last_used = int(time.time())`
- In `update_and_store()`: set `obj.last_used = int(time.time())` on the cast `_SqlCharacterData` object before `fields_to_update` is built (Peewee syncs `obj.__data__` automatically on attribute assignment)
- In `SqlState.__init__()`: replace the existing `creation_time` migration block with:

```python
with self._db.connection_context():
    cursor = self._db.execute_sql("PRAGMA table_info(_sqlcharacterdata);")
    columns = [row[1] for row in cursor.fetchall()]
    if "creation_time" in columns and "last_used" not in columns:
        # Rename migration: add last_used and backfill with grace-period value
        self._db.execute_sql(
            "ALTER TABLE _sqlcharacterdata ADD COLUMN last_used INTEGER DEFAULT NULL;"
        )
        half_threshold_ago = int(time.time()) - CORE_CFG.prune_threshold_days * 86400 // 2
        self._db.execute_sql(
            "UPDATE _sqlcharacterdata SET last_used = ? WHERE last_used IS NULL;",
            (half_threshold_ago,),
        )
    elif "last_used" not in columns:
        # No prior creation_time column — just add last_used
        self._db.execute_sql(
            "ALTER TABLE _sqlcharacterdata ADD COLUMN last_used INTEGER DEFAULT NULL;"
        )
```

### Notes

- Old JSON records have `creation_time` as a key that Pydantic silently ignores after the rename, leaving `last_used=None`. The migration in `__init__` catches these and sets the grace-period value.
- The SQL migration runs at every startup but `ALTER TABLE` only executes when the column is absent; the `UPDATE` backfill is guarded by the same condition, so it also only runs once.
- After this stage, `grep -rn "creation_time" packages/` should return zero results.

### Verification

- Run `pytest tests/` — all existing tests pass
- Add tests in `tests/test_state_persistence.py`:
  - Create a character, call `update_and_store`, reload state, assert `last_used` ≈ `int(time.time())`
  - Load state from a fixture JSON file with `creation_time` key (absent `last_used`) and assert `last_used` is set to approximately `now - threshold/2`
  - Run both assertions against JSON and SQLite backends

---

## Stage 2: Core config and pruning utility

**Goal:** Centralise the pruning threshold in the core package so all frontend applications share the same setting.

### Files to create/modify

**`packages/initbot-core/src/initbot_core/config.py`** (new file, AGPL header)

```python
from pydantic import Field
from pydantic_settings import BaseSettings

class CoreSettings(BaseSettings):
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }
    prune_threshold_days: int = Field(
        default=90,
        description="Characters not used in this many days are eligible for pruning.",
    )

CORE_CFG = CoreSettings()
```

**`.env`** (create if absent, otherwise append)

- Add `PRUNE_THRESHOLD_DAYS=90`
- Both `initbot-chat` (`.env` + `.env.chat`) and `initbot-web` (`.env` + `.env.web`) already load `.env`, so the setting is available to both frontends automatically. `WebSettings.extra = "ignore"` means the web app silently ignores it until it needs it.

**`packages/initbot-core/src/initbot_core/pruning.py`** (new file, AGPL header)

```python
import time
from initbot_core.data.character import CharacterData

def is_eligible_for_pruning(cdi: CharacterData, threshold_days: int) -> bool:
    """Returns True if the character has not been used recently enough."""
    if cdi.last_used is None:
        return True
    return cdi.last_used < int(time.time()) - threshold_days * 86400
```

The function accepts `threshold_days` as a parameter (not importing config directly) to keep it pure and trivially testable.

### Verification

- New `tests/test_pruning.py`: unit test `is_eligible_for_pruning` with `last_used=None`, an old timestamp, and a recent timestamp — no fixtures needed

---

## Stage 3: New chat commands — `unused`, `prune`, `touch`

**Goal:** Give players command-line tools to inspect and act on pruning eligibility.

### Command design decision

`prune` is a **new command separate from `remove`**. `remove` is a targeted single-character operation; `prune` is a bulk criterion-based sweep. Keeping them distinct avoids accidental bulk deletions and makes each command's intent self-evident.

Arguments use plain words with no `-` or `--` prefix, consistent with existing commands.

### Files to modify

**`packages/initbot-chat/src/initbot_chat/commands/character.py`**

Add imports:

```python
from initbot_core.config import CORE_CFG
from initbot_core.pruning import is_eligible_for_pruning
```

Add three new commands before the `char_error` handler.

**`unused [all_players]`** — list eligible characters:

```python
@commands.command(usage="[all_players]")
async def unused(ctx: Any, *args: str) -> None:
    """Lists characters eligible for pruning (unused beyond the configured threshold).

    By default, only lists the requesting player's own characters.
    Pass 'all_players' to list eligible characters belonging to any player."""
    show_all = "all_players" in args
    threshold = CORE_CFG.prune_threshold_days
    eligible = [
        cdi for cdi in ctx.bot.initbot_state.characters.get_all()
        if is_eligible_for_pruning(cdi, threshold)
        and (show_all or cdi.user == ctx.author.name)
    ]
    if not eligible:
        await ctx.send("No characters eligible for pruning.", delete_after=5)
        return
    parts = (f"- **{cdi.name}** (_{cdi.user}_)\n" for cdi in eligible)
    await send_in_parts(ctx, parts)
```

**`prune [all_players]`** — remove eligible characters:

```python
@commands.command(usage="[all_players]")
async def prune(ctx: Any, *args: str) -> None:
    """Removes all characters eligible for pruning (unused beyond the configured threshold).

    By default, only prunes the requesting player's own characters.
    Pass 'all_players' to prune eligible characters belonging to any player.
    Always replies with the names of the pruned characters."""
    show_all = "all_players" in args
    threshold = CORE_CFG.prune_threshold_days
    to_prune = [
        cdi for cdi in ctx.bot.initbot_state.characters.get_all()
        if is_eligible_for_pruning(cdi, threshold)
        and (show_all or cdi.user == ctx.author.name)
    ]
    for cdi in to_prune:
        ctx.bot.initbot_state.characters.remove_and_store(cdi)
    if not to_prune:
        await ctx.send("No characters to prune.", delete_after=5)
        return
    await ctx.send("Pruned: " + ", ".join(cdi.name for cdi in to_prune))
```

Note: `get_all()` is evaluated into a list before the loop to avoid mutating a live sequence during iteration.

**`touch [character name] [character name] ...`** — reset `last_used` to now for one or more characters:

```python
@commands.command(usage="[character name] [character name ...]")
async def touch(ctx: Any, *args: str) -> None:
    """Marks one or more characters as recently used, resetting their pruning eligibility timer.

    Each argument is treated as a separate character name or abbreviation.
    If the Discord user manages only a single character, the character name is optional.

    The character name can be an abbreviation.
    For example, if the full name of a character is "Mediocre Mel", then typing "Med" is sufficient.
    That's as long as no other character name starts with "Med"."""
    tokens: tuple = args if args else ((),)
    touched = []
    for token in tokens:
        name_arg = (token,) if token else ()
        cdi: CharacterData = ctx.bot.initbot_state.characters.get_from_tokens(
            name_arg, ctx.author.name
        )
        ctx.bot.initbot_state.characters.update_and_store(cdi)
        touched.append(cdi.name)
    await ctx.send(
        "Marked as recently used: " + ", ".join(touched),
        delete_after=3,
    )
```

Each positional arg is passed individually as a single-element token list to `get_from_tokens`. When no args are given, an empty token list is passed so `get_from_tokens` can use its existing single-character disambiguation. Multi-word character names must be abbreviated to a single unambiguous prefix when passing multiple names at once.

Add `@unused.error`, `@prune.error`, `@touch.error` to the `char_error` decorator stack.

Also: exclude `last_used` from the settable attributes in `set_` by filtering it out of `char_fields` — it is auto-maintained and exposing a raw Unix timestamp would be confusing.

**`packages/initbot-chat/src/initbot_chat/commands/__init__.py`**

- Import `prune`, `touch`, `unused` from `character`
- Add to the `commands` frozenset

### Verification

New `tests/test_commands_pruning.py` using the `mock_ctx` fixture:

- `test_unused_own`: two old characters for `testuser` appear
- `test_unused_excludes_other_player`: other player's character absent without `all_players`
- `test_unused_all_players_flag`: both players' characters appear with `"all_players"` arg
- `test_unused_empty`: no eligible chars → "No characters" message
- `test_prune_removes`: old character is gone after prune, response contains name
- `test_prune_spares_recent`: character with `last_used=int(time.time())` survives
- `test_touch_single`: character with `last_used=0` has updated timestamp after `touch.callback(mock_ctx, "charname")`
- `test_touch_multiple`: two characters both updated after `touch.callback(mock_ctx, "char1", "char2")`
- `test_touch_no_args`: works for user with a single character (no args)

---

## Stage 4: Monthly pruning notification task

**Goal:** Proactively remind players once a month about their unused characters via Discord DM.

### Files to modify

**`packages/initbot-chat/src/initbot_chat/bot.py`**

Add imports: `from collections import defaultdict`, `from initbot_core.config import CORE_CFG`, `from initbot_core.pruning import is_eligible_for_pruning`

Add new task after `_vulnerability_check`:

```python
@tasks.loop(hours=24 * 30)
async def _pruning_notification() -> None:
    all_chars = bot.initbot_state.characters.get_all()  # type: ignore
    threshold = CORE_CFG.prune_threshold_days
    by_user: dict[str, list] = defaultdict(list)
    for cdi in all_chars:
        if is_eligible_for_pruning(cdi, threshold):
            by_user[cdi.user].append(cdi)

    for username, chars in by_user.items():
        member = None
        for guild in bot.guilds:
            member = guild.get_member_named(username)
            if member:
                break
        if not member:
            _log.warning("Could not find guild member for pruning notification: %s", username)
            continue
        names_list = "\n".join(f"- {c.name}" for c in chars)
        try:
            await member.send(
                f"Hi! The following characters you own haven't been used in over "
                f"{threshold} days:\n{names_list}\n\n"
                f"You have a few options:\n"
                f"1. Do nothing — you'll get another reminder next month.\n"
                f"2. Use `$prune` to remove all your unused characters at once.\n"
                f"3. Use `$touch <character name>` to mark a character as recently used "
                f"if you'd like to keep it."
            )
        except Exception:
            _log.warning("Could not send pruning notification DM to %s", username)
```

In `on_ready()`, start the pruning task **before** the `alert_channel_id` guard checks (the task uses DMs, not a channel, so it should run even when `alert_channel_id` is set to the ignore sentinel):

```python
async def on_ready():
    ...
    if not _pruning_notification.is_running():
        _pruning_notification.start()

    if CFG.alert_channel_id == _IGNORE_SENTINEL:  # existing guard
        ...
```

### Note on `guild.get_member_named()`

This uses the local member cache. With `Intents.default()` (as currently configured), coverage depends on members the bot has "seen." For a small server this is usually sufficient. DM failures are logged as warnings. The `members` privileged intent can be enabled later if comprehensive coverage is needed.

### Verification

New `tests/test_bot_pruning.py`:

- `test_pruning_notification_sends_dm`: mock state with two old characters for the same user; mock a guild member with `send=AsyncMock()`; call `_pruning_notification.coro()`; assert `member.send` called once with a message containing both character names and `$prune`
- `test_pruning_notification_member_not_found`: mock `guild.get_member_named()` → `None`; assert `_log.warning` called, no exception
- `test_pruning_notification_dm_blocked`: mock `member.send` raises `Exception`; assert warning logged, loop continues to next user
- `test_pruning_notification_skips_recent`: character with `last_used=int(time.time())` does not trigger a DM

---

## Critical files

| File | Change |
| ---- | ------ |
| `packages/initbot-core/src/initbot_core/data/character.py` | Rename `creation_time` → `last_used` |
| `packages/initbot-core/src/initbot_core/models/character.py` | Rename property |
| `packages/initbot-core/src/initbot_core/state/local.py` | Rename field; set on add + update; migrate `None` records on load |
| `packages/initbot-core/src/initbot_core/state/sql.py` | Rename field; DB migration with backfill; set on add + update |
| `packages/initbot-core/src/initbot_core/config.py` | **New**: `CoreSettings` with `prune_threshold_days` |
| `packages/initbot-core/src/initbot_core/pruning.py` | **New**: `is_eligible_for_pruning` predicate |
| `.env` | **New/updated**: `PRUNE_THRESHOLD_DAYS=90` |
| `packages/initbot-chat/src/initbot_chat/commands/character.py` | Add `unused`, `prune`, `touch`; exclude `last_used` from `set_` |
| `packages/initbot-chat/src/initbot_chat/commands/__init__.py` | Register new commands |
| `packages/initbot-chat/src/initbot_chat/bot.py` | Add `_pruning_notification` task |

## Reusable utilities

- `get_from_tokens()` — existing fuzzy character name resolution (used by `touch`)
- `send_in_parts()` — existing chunked message sender (used by `unused`)
- `remove_and_store()` / `update_and_store()` — existing persistence methods
- `@tasks.loop()` — existing discord.py periodic task pattern
- `mock_ctx` fixture — existing test fixture pattern for all new command tests
