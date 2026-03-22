# mypy Alternatives Comparison

mypy is relatively slow, especially for pre-commit hooks. This document compares
four faster alternatives — pyright, ty, pyrefly, and zuban — against the
current codebase to guide a potential migration.

## Methodology

Each checker was run against the 42 source files in the three packages
(`initbot-core`, `initbot-chat`, `initbot-web`) using the project's own `.venv`
for import resolution, with no tool-specific configuration file. All timings are
wall-clock on a single run including tool startup.

## Results

| Checker | Errors | Warnings | Wall time |
|---------|--------|----------|-----------|
| mypy (baseline) | 0 | 0 | 0.54 s |
| ty 0.0.24 | 7 | 0 | 0.30 s |
| pyrefly 0.57.1 | 2 | 1 | 0.36 s |
| zuban 0.6.1 | 3 | 0 | 0.86 s |
| pyright (latest) | 7 | 0 | 2.12 s |

ty and pyrefly are the fastest. pyright is slower than mypy on a codebase this
small because Node.js startup dominates.

## Issue coverage

| Issue | mypy | ty | pyright | pyrefly | zuban |
|-------|------|----|---------|---------|-------|
| `_meta` undeclared attribute (`state/sql.py:147`) | — | ✓ | ✓ | ✓ | ✓ |
| 6× `import_from` override violates LSP (`state/state.py`) | — | ✓ | ✓ | — | — |
| Generator/dict type mismatch (`state/factory.py:16`) | — | — | — | ✓ | ✓ |
| Ambiguous variadic-tuple slice (`commands/luck.py:38`) | — | — | — | — | ✓ |
| Redundant `cast()` (`state/sql.py:365`) | — | — | — | ⚠ | — |

All findings are genuine issues; none are false positives.

## Issue details

### `_meta` undeclared attribute (all four checkers)

`type(obj)._meta` in `state/sql.py:147` accesses Peewee's runtime metadata
attribute, which is not declared in the type stubs. Requires one `# type:
ignore[attr-defined]` or a proper cast/Protocol fix.

### `import_from` LSP violation (ty and pyright only)

`PartialState.import_from` is declared `def import_from(self, src: Self) ->
None`. Six concrete subclasses (`AbilityState`, `AugurState`, `CharacterState`,
`OccupationState`, `ClassState`, `CritState`) narrow `src` to their own type
rather than keeping `Self`, violating the Liskov Substitution Principle. mypy
accepts this silently. The fix is to use `Self` consistently in the subclasses,
which is semantically correct since each subclass can only import from an
instance of itself.

### Generator/dict type mismatch (pyrefly and zuban)

`state/factory.py:14–19` constructs a `dict` from a `chain.from_iterable(...)`
that yields `tuple[str, type[State]]`, but the declared type requires
`Callable[[str], State]` as the value. pyrefly reports `no-matching-overload`
and zuban reports an incompatible generator item type. Requires either a
corrected type annotation or a `cast`.

### Ambiguous variadic-tuple slice (zuban only)

`commands/luck.py:38`: `args[0:-1]` where `args: tuple[str, ...]`. Slicing a
homogeneous variadic tuple with a runtime-dependent range is considered
ambiguous by zuban. Requires a `# type: ignore` or rewriting the slice to
avoid the negative index.

### Redundant `cast()` (pyrefly only)

`state/sql.py:365`: `cast(type[Model], i)` casts to the same type the
expression already has. Can simply be removed.

## Existing suppressions

The codebase currently has four `# type: ignore` comments, none of which
overlap with the above issues:

- `base.py:12` — `asdict(self)` return type
- `config.py:42` — pydantic-settings `_env_file` kwarg
- `bot.py:134` — dynamic `initbot_state` attribute on the bot
- `app.py:56` — pydantic-settings `_cli_parse_args` kwarg

These suppressions remain valid under all four alternative checkers.

## Recommendation

**ty** is the best replacement for mypy:

- Fastest wall-clock time (0.30 s vs mypy's 0.54 s).
- Catches the most semantically significant issues (the six LSP violations in
  `state.py` that mypy silently accepts).
- Rust-based; integrates naturally with the existing ruff/uv toolchain.
- Actively developed by Astral.

**Adoption cost:** 7 fixes — fixing the `import_from` overrides to use `Self`
(desirable cleanup regardless) and adding one `# type: ignore[attr-defined]`
for the Peewee `_meta` access.

pyright is equivalent to ty in strictness but offers no speed benefit on this
codebase and adds a Node.js dependency. pyrefly and zuban are interesting but
miss the LSP violations, providing weaker guarantees.
