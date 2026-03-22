# Analysis: Protocol vs Dataclass for Data Layer

## Context

The data layer (`initbot_core/data/`) defines types like `CharacterData` as concrete `@dataclass` subclasses of `BaseData`. Storage implementations (`_SqlCharacterData` via Peewee, `LocalCharacterData` via Pydantic) are structurally equivalent but unrelated types. The code bridges them with `cast()` calls, suppressing type checker errors rather than satisfying them. Application code then receives storage-native objects masked as `CharacterData`, and the false dataclass identity causes:

- `asdict(char_data)` works only when the object truly is a dataclass (only on the "input" side of `add_store_and_get`)
- `BaseData.as_dict()` calls `dataclasses.asdict(self)` which would fail on Peewee/Pydantic objects
- `update_and_store` and `remove_and_store` must do `isinstance` checks against the concrete storage type to recover the real object

## The Core Insight: Two Different Roles Under One Name

`CharacterData` currently serves two distinct roles:

1. **Creation input** — a dataclass instantiated in the chat/web layer (`CharacterData(name=…, user=…)`), passed into `add_store_and_get`
2. **Data handle** — the storage-native object returned by `get_all()` and mutated in place via the `Character` domain class

These have fundamentally different requirements. The Protocol refactoring is really about making the **data handle** role honest.

---

## Pros of Using `Protocol`

### 1. Honest structural typing
`_SqlCharacterData` and `LocalCharacterData` would *genuinely* satisfy the `Protocol` — the type checker verifies field presence and types rather than the code lying with `cast()`. The `cast(Sequence[CharacterData], ...)` calls in every `get_all()` become unnecessary.

### 2. Eliminates false dataclass affordances
Application code receiving a `CharacterData` currently might assume `dataclasses.asdict()`, `dataclasses.fields()`, or `dataclasses.replace()` work on it — but they don't when the concrete object is Peewee/Pydantic. A Protocol is explicitly *just* an interface with no implicit operations.

### 3. `BaseData` / `as_dict()` problem surfaces cleanly
The `BaseData.as_dict()` method calling `dataclasses.asdict(self)` is already broken for storage-returned objects. Making `CharacterData` a Protocol removes the `BaseData` inheritance and makes you handle serialization explicitly — which is actually what the code already needs.

### 4. Mutable attribute protocols work naturally
Python `Protocol` supports mutable attributes. The `Character` domain class doing `self.cdi.name = name`, `self.cdi.level = level` is representable as protocol attributes — the type checker can verify the concrete types provide writable fields.

### 5. `isinstance` via `@runtime_checkable`
With `@runtime_checkable`, `isinstance(obj, CharacterData)` checks attribute presence. The existing `isinstance(char_data, _SqlCharacterData)` / `isinstance(char_data, LocalCharacterData)` guards in `update_and_store` / `remove_and_store` are unaffected.

---

## Cons / Problems

### 1. Protocols cannot be instantiated — creation sites break
The chat/web layer calls `CharacterData(name=…, user=…)` directly. A Protocol is not instantiable. You would need a separate concrete class for the creation input:

```python
@dataclass
class NewCharacterData:      # creation input — a plain dataclass
    name: str
    user: str
    active: bool = True
    …

class CharacterData(Protocol):   # data handle — what the store returns
    name: str
    user: str
    active: bool
    …
```

`add_store_and_get` signature becomes `(self, char_data: NewCharacterData) -> CharacterData`. This is arguably cleaner (it separates creation from retrieval) but requires refactoring all creation sites.

### 2. `asdict()` calls in storage implementations break for the creation path
`sql.py:132` calls `asdict(char_data)` on the incoming `NewCharacterData` — fine, it's still a dataclass.
`local.py:161` calls `asdict(char_data)` for the same reason — also fine.

But `BaseData.as_dict()` (used in export/import via `.as_dict()`) is called on storage-returned objects. This is *already broken* for `_SqlCharacterData`/`LocalCharacterData` (neither is a dataclass). Moving to Protocol makes the bug impossible to miss — which is a pro disguised as a con.

### 3. Protocols cannot express default values
`active: bool = True` in a Protocol is a syntax error. Defaults live in concrete implementations only. This is not a real problem for the interface, just a difference in expressiveness.

### 4. `@runtime_checkable` only checks attribute presence, not types
If you add `@runtime_checkable`, `isinstance(obj, CharacterData)` only checks that `name`, `user`, etc. exist as attributes — not their types. This is the same level of guarantee the current `cast()` gives, so no regression.

### 5. Tooling / IDE support is slightly weaker
Autocomplete and "find usages" work fine for Protocol attributes, but refactoring tools that understand dataclass field positions or `dataclasses.replace()` calls won't apply.

---

## Summary Table

| Concern | Current dataclass | Protocol |
|---|---|---|
| Type checker verifies storage ↔ interface match | No (`cast()` suppresses) | Yes |
| `asdict()` works on returned objects | No (silently broken) | N/A (not implied) |
| Instantiation at creation sites | Works | Breaks (needs `NewCharacterData`) |
| `isinstance` guards in update/remove | Work (concrete type) | Work (unchanged or `@runtime_checkable`) |
| `Character` domain mutation (`cdi.name = …`) | Works | Works |
| `BaseData.as_dict()` on returned objects | Broken (masked) | Removed entirely |
| Structural clarity | False (dataclass features implied) | Accurate |

---

## Recommendation

The Protocol approach accurately models the actual boundary: the data layer defines what shape a data handle must have; the storage layer owns the concrete implementations. The main cost is splitting `CharacterData` into a `Protocol` (for reading/mutation) and a `NewCharacterData` dataclass (for creation input), plus removing `BaseData`'s reliance on `dataclasses.asdict()`.

The refactoring scope is moderate:
- `data/character.py` (and all other data files) → convert to Protocol
- Creation sites in `initbot_chat` and `initbot_web` → use `NewCharacterData`
- `add_store_and_get` signatures → accept `NewCharacterData`
- `BaseData` → remove or redesign (`.as_dict()` must be part of the Protocol or handled separately per implementation)
- `cast()` calls in every `get_all()` → delete

## Critical files

- [data/character.py](packages/initbot-core/src/initbot_core/data/character.py)
- [base.py](packages/initbot-core/src/initbot_core/base.py)
- [state/local.py](packages/initbot-core/src/initbot_core/state/local.py)
- [state/sql.py](packages/initbot-core/src/initbot_core/state/sql.py)
- [models/character.py](packages/initbot-core/src/initbot_core/models/character.py)
- [initbot_chat/commands/character.py](packages/initbot-chat/src/initbot_chat/commands/character.py)
