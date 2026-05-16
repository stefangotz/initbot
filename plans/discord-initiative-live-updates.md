# Plan: Live-updating $inis response

## Context

`$inis` posts a Discord embed listing active characters sorted by initiative. Once posted it is static — players must re-run `$inis` to see changes. The goal is to keep the most-recently-posted `$inis` embed live: whenever a command that changes the initiative list runs within one hour of the last `$inis`, the bot edits that embed in place.

## Architecture

- Store the last `$inis` message reference (message ID, channel ID, timestamp) **per guild** on the bot object, as `bot.last_inis_message: dict[int, LiveInisRef]`.
- Tracking is in-memory only. A 1-hour TTL makes persistence across restarts unnecessary.
- The embed-building logic (currently inline in `inis()`) is extracted into `build_inis_embed(state)` so both the `$inis` send path and the edit refresh path share one implementation.
- `build_inis_embed` and `refresh_live_inis` go in **`utils.py`** — the one module both `init.py` and `character.py` can import without creating a cycle (`utils.py` ← `character.py` ← `init.py`).

## Commands that trigger a refresh

| Command | Reason |
|---------|--------|
| `$init` | changes initiative value |
| `$remove` | removes character from list |
| `$rename` | changes displayed name |
| `$prune` | batch-removes characters (only when something was pruned) |
| `$touch` | updates `last_used`, can restore a character to the 24 h window |

`$init_dice` only sets a dice spec, not the current value — no refresh needed.

## Implementation steps

### 1. `utils.py` — add three new items

New imports needed: `import logging`, `from datetime import datetime`, `import discord`, `from discord import Embed`, `from dataclasses import dataclass`.

**a. `build_inis_embed(state: State) -> Embed`**

Extract the embed logic from `inis()` verbatim. Filters characters with `last_used` within 24 h and a non-None initiative; sorts descending by initiative; builds the "N: **Name** (*player*)" description.

**b. `@dataclass class LiveInisRef`** with fields `message_id: int`, `channel_id: int`, `posted_at: int`.

**c. `async def refresh_live_inis(ctx: Context) -> None`**

- Short-circuit if `ctx.guild is None`.
- Look up `ctx.bot.last_inis_message.get(guild_id)`.
- If missing or `time.time() - ref.posted_at >= 3600`: clear the entry and return.
- `channel = ctx.bot.get_channel(ref.channel_id)` — if `None`, clear and return.
- `msg = await channel.fetch_message(ref.message_id)`; `await msg.edit(embed=build_inis_embed(...))`.
- `discord.NotFound` → log warning, clear entry.
- `discord.HTTPException` → log warning, **keep** entry (transient error; next command can retry).

### 2. `init.py` — update `inis()` and `init()`

- Replace inline embed construction with `build_inis_embed(ctx.bot.initbot_state)`.
- Capture returned message: `msg = await ctx.send(embed=embed)`.
- If `ctx.guild is not None and msg is not None`: store `LiveInisRef(msg.id, ctx.channel.id, int(time.time()))` in `ctx.bot.last_inis_message[ctx.guild.id]`.
- At the end of `init()` (after `ctx.send`): `await refresh_live_inis(ctx)`.
- Remove the now-unused `characters` import from `init.py` (the `characters()` helper was only used inside `inis()`).
- Add to imports from `utils`: `build_inis_embed`, `LiveInisRef`, `refresh_live_inis`.
- Add `import time` to `init.py`.

### 3. `character.py` — add `refresh_live_inis` calls

Add `refresh_live_inis` to the existing `utils` import line.

Add `await refresh_live_inis(ctx)` after the success `ctx.send` in:

- `rename()` — after "Renamed …"
- `remove()` — after "Removed character …"
- `touch()` — after "Marked as recently used …"
- `prune()` — **only** inside the `if to_prune:` branch, after "Pruned: …". The nothing-to-prune branch needs no refresh.

### 4. `bot.py` — initialise `bot.last_inis_message`

In `run()`, after `bot.initbot_state = create_state_from_source(...)`:

```python
bot.last_inis_message = {}  # type: ignore  # dict[int, LiveInisRef], keyed by guild id
```

### 5. `tests/conftest.py` — update `mock_ctx` fixture

```python
ctx.bot.last_inis_message = {}
ctx.guild.id = 999000000000000001
ctx.channel.id = 888000000000000001
ctx.bot.get_channel = MagicMock(
    return_value=None
)  # refresh_live_inis no-ops in existing tests
mock_message = MagicMock()
mock_message.id = 777000000000000001
mock_message.edit = AsyncMock(return_value=None)
ctx.send = AsyncMock(return_value=mock_message)
```

`ctx.bot.get_channel = MagicMock(return_value=None)` makes `refresh_live_inis` short-circuit in all existing tests (channel lookup returns None → no fetch/edit). Tests that need to verify editing wire up their own channel mock.

All existing tests remain valid: `assert_called_once()`, `call_args.kwargs["embed"]`, `call_args[0][0]` all still work.

### 6. New test file: `tests/test_live_inis.py`

| Test | What it verifies |
|------|-----------------|
| `test_inis_stores_message_ref` | After `inis.callback`, `bot.last_inis_message[guild_id]` has correct `message_id`, `channel_id`, `posted_at` |
| `test_init_refreshes_live_embed` | After storing a fresh ref, `init.callback` calls `msg.edit(embed=...)` |
| `test_remove_refreshes_live_embed` | Same for `remove.callback` |
| `test_rename_refreshes_live_embed` | Same for `rename.callback` |
| `test_prune_refreshes_live_embed` | Same for `prune.callback` when characters exist |
| `test_prune_no_refresh_when_nothing_pruned` | `prune` with no eligible characters → `edit` not called |
| `test_touch_refreshes_live_embed` | Same for `touch.callback` |
| `test_refresh_skips_expired_ref` | `posted_at = time.time() - 3601` → edit not called, ref cleared |
| `test_refresh_clears_on_not_found` | `fetch_message` raises `discord.NotFound` → ref cleared, no exception |
| `test_refresh_keeps_ref_on_http_exception` | `fetch_message` raises `discord.HTTPException` → ref preserved, no exception |
| `test_refresh_no_guild` | `ctx.guild = None` → no crash |
| `test_inis_overwrites_previous_ref` | Second `$inis` replaces the first ref |

## Critical files

| File | Change |
|------|--------|
| `packages/initbot-chat/src/initbot_chat/commands/utils.py` | Add `build_inis_embed`, `LiveInisRef` dataclass, `refresh_live_inis` |
| `packages/initbot-chat/src/initbot_chat/commands/init.py` | Use `build_inis_embed`; store returned message; call `refresh_live_inis` after `$init` |
| `packages/initbot-chat/src/initbot_chat/commands/character.py` | Call `refresh_live_inis` after `$remove`, `$rename`, `$prune` (pruned branch), `$touch` |
| `packages/initbot-chat/src/initbot_chat/bot.py` | Initialise `bot.last_inis_message = {}` in `run()` |
| `tests/conftest.py` | Add guild/channel IDs, `last_inis_message`, mock message with `.edit`, `get_channel` stub |
| `tests/test_live_inis.py` | New file with 12 test cases |

## Edge cases

- **DM context** (`ctx.guild is None`): `refresh_live_inis` short-circuits immediately.
- **Message deleted**: `discord.NotFound` caught, ref cleared.
- **Channel gone / bot lost access**: `get_channel()` returns `None`, ref cleared.
- **Concurrent `$inis`**: last call wins — guild key is overwritten.
- **Two guilds**: separate keys, no cross-contamination.
- **`prune` with nothing to prune**: refresh not called; unchanged embed not sent.
- **TTL boundary**: `>=` means exactly one hour old is treated as expired.

## Verification

```bash
uv run pytest tests/test_live_inis.py tests/test_commands_init.py -q
uv run ruff check packages/initbot-chat/src/initbot_chat/commands/
uv run ty check packages/initbot-chat/src/
```
