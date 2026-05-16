# Web App / Chat Bot Gap Analysis

High-level worksheet for closing functional gaps between the two applications.
Each row is a feature area; gaps are noted in the relevant column.

## Initiative

| Feature | Chat bot | Web app |
|---------|----------|---------|
| Set initiative (explicit value) | `$init [char] N` | ✓ inline edit |
| Set initiative dice spec | `$init_dice [char] spec` | ✓ inline edit |
| Roll initiative from dice spec | via `$init [char]` (omit value) | ✓ roll button |
| View initiative order | `$inis` (snapshot, last 24 h) | ✓ live, auto-updating |
| Re-sort after out-of-band changes | — | ✓ resort button |
| Stale-initiative indicator | — | ✓ visual indicator |

## Characters

| Feature | Chat bot | Web app |
|---------|----------|---------|
| Create character | implicit via `$init` / `$init_dice` | ✓ create row |
| Delete character | `$remove [char]` | ✓ delete button |
| Rename character | `$rename [old] new` | ✓ inline edit |
| Reassign character to different player | — | ✓ player dropdown |
| View one character's full detail | `$char [char]` | — (no last-used, no single-char view) |
| List all characters with player | `$chars` | ✓ tracker table |

## Character maintenance (pruning)

The pruning workflow has no web equivalent.

| Feature | Chat bot | Web app |
|---------|----------|---------|
| List stale characters | `$unused [all_players]` | — |
| Delete stale characters | `$prune [all_players]` | — |
| Mark characters as recently used | `$touch [char...]` | — |

## Action templates

The actions system has no web equivalent.

| Feature | Chat bot | Web app |
|---------|----------|---------|
| List character actions | `$actions [char] list` | — |
| Add action template | `$actions [char] add TEMPLATE` | — |
| Update action template | `$actions [char] update IDX TEMPLATE` | — |
| Remove action template | `$actions [char] remove IDX` | — |
| Execute action (resolve dice) | `$act [char] NR` | — |

## Dice rolling

| Feature | Chat bot | Web app |
|---------|----------|---------|
| Ad-hoc dice roll (not tied to a character) | `$roll expr` | — |

## Miscellaneous

| Feature | Chat bot | Web app |
|---------|----------|---------|
| Random tarot card | `$tarot` | — |
| Web app login link | `$web` | n/a (entry point) |
