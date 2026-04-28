# Applying qmail's design to initbot

## Context

This is a design exploration: what would initbot look like if it were rebuilt around DJB's qmail principles — minimal trusted code base, strict process decomposition, least privilege per component, atomic file-queue operations, and explicit acceptance semantics?

Initbot today (per `packages/initbot-{core,chat,web}/`) is two processes sharing one SQLite file:
- `initbot-chat` — discord.py bot, holds the Discord token, accepts arbitrary user commands, writes to SQLite directly.
- `initbot-web` — Starlette/Datastar app, accepts HTTP input, writes to SQLite directly, validates web login tokens.
- Cross-process notifications via UDP zero-byte datagrams to localhost.

Trust boundaries that exist but are not enforced by process separation:
- Discord input → bot process → DB writer → Discord token holder (all one process).
- HTTP input → web process → DB writer → session-key holder (all one process).
- OSV API fetches happen inside the same processes that hold credentials.

A compromise of either main process today yields: full DB write, the Discord bot token, the web session signing key, and outbound network. The qmail-style refactor's purpose is to make that blast radius dramatically smaller.

This document is a design proposal, not an implementation plan. For an RPG initiative tracker this level of decomposition is plainly overkill — included at the end is a "how much of this is worth doing" section.

## Mapping qmail's roles onto initbot

| qmail role | initbot analogue | responsibility |
|------------|------------------|----------------|
| `qmail-smtpd` | `ib-discord-recv` | Read Discord events, parse, validate. Holds *read* side of Discord token only. |
| `qmail-smtpd` (HTTP variant) | `ib-web-recv` | Accept HTTP form/SSE input, validate. No secrets. |
| `qmail-queue` | `ib-queue` | The **only** writer to `queue/todo/`. Validates command envelope. Tiny. The single setgid bridge. |
| `qmail-send` | `ib-send` | Queue manager. Watches `todo/`, moves to `active/`, spawns workers, retries, bounces. |
| `qmail-local` | `ib-apply` | The **only** writer to the SQLite DB. Applies one command at a time. No network. |
| `qmail-remote` | `ib-discord-send` | Posts to Discord. Holds the Discord *write* token. No DB access. |
| `qmail-remote` (HTTP) | `ib-web-render` | Serves HTML/SSE responses. Read-only DB. |
| `qmail-clean` | `ib-prune` | Periodic janitor: prunes expired tokens, stale characters. Read-only outside of bounded delete commands enqueued like everyone else. |
| (no analogue) | `ib-osv-fetch` | Outbound HTTPS to api.osv.dev. No DB, no secrets. Pipes results to `ib-vuln-process`. |
| (no analogue) | `ib-vuln-process` | Parses OSV JSON in a no-network sandbox. Emits queue commands. |

## Major functional components and Unix users

Each component runs as a dedicated user, mirroring `qmaild`/`qmailq`/`qmailr`/`qmails`/`qmaill`:

- `ibrecv` — runs `ib-discord-recv` and `ib-web-recv`. Network read, no DB, no write tokens.
- `ibq` — runs `ib-queue`. Setgid-to-`ibqueue`. Owns `queue/todo/`. Only writer there.
- `ibs` — runs `ib-send`. Reads `queue/todo/`, `queue/active/`. Spawns workers.
- `ibstate` — runs `ib-apply`. Owns the SQLite file. Only writer to it. No network, no secrets.
- `ibdiscord` — runs `ib-discord-send`. Holds Discord write token. No DB.
- `ibwww` — runs `ib-web-render`. Read-only DB. Serves HTTP. No write token. Holds short-lived signed-cookie key only.
- `ibnet` — runs `ib-osv-fetch`. Outbound HTTPS only. No DB, no secrets, no IPC except a single output pipe.
- `ibvuln` — runs `ib-vuln-process`. No network. Reads from `ibnet`'s pipe, emits queue commands.

Filesystem layout:

```
/var/lib/initbot/
  queue/
    todo/        # owner ibq, mode 0700 — only ib-queue writes here
    active/      # owner ibs, mode 0700
    bounce/      # owner ibs, mode 0700
    replies/     # owner ibstate, mode 0750 (group ibsend) — ib-discord-send/ib-web-render read
  state/
    initbot.sqlite  # owner ibstate, mode 0640 (group ibwww) — ibwww reads, ibstate writes
  secrets/
    discord-write.token  # owner ibdiscord, mode 0400
    discord-read.token   # owner ibrecv,    mode 0400
    session-signing.key  # owner ibwww,     mode 0400
```

Each command in `queue/todo/$id` is a self-contained envelope (sender identity, command verb, validated arguments, reply destination) written via `write tmp + fsync(tmp) + fsync(dir) + rename` — the same atomicity pattern as qmail's `queue/mess` and as Maildir.

## Data flows

### Inbound Discord command (e.g. `$init Aldric 17`)

1. `ib-discord-recv` (user `ibrecv`) receives the gateway event. It parses, normalises the character name, resolves the player from the Discord ID, and produces a structured `INIT_SET` envelope.
2. It pipes the envelope over a Unix socket to `ib-queue` (user `ibq`). `ib-queue` re-validates the envelope schema, writes `queue/todo/$id.tmp`, `fsync`s, `rename()`s to `queue/todo/$id`, `fsync`s the directory, and returns success on the socket.
3. `ib-discord-recv` only **then** ACKs the gateway event. This is qmail's acceptance rule: once we've said "yes" to Discord, the command is committed to either applying or bouncing.
4. `ib-send` notices the new file (inotify or poll), moves it to `queue/active/$id`, and `fork+exec`s `ib-apply` with the file descriptor.
5. `ib-apply` (user `ibstate`) reads the envelope, executes a single SQL transaction, writes `queue/replies/$id` describing what to tell the user, and exits 0.
6. `ib-send` spawns `ib-discord-send` (user `ibdiscord`), which reads the reply file and posts to Discord using the *write* token. On success → `queue/done/`; on transient failure → backoff retry; on permanent failure → `queue/bounce/` plus a bounce reply.

### Inbound HTTP mutation (e.g. edit initiative in tracker)

Identical pipeline, only the entry point differs: `ib-web-recv` pipes to `ib-queue`, the reply is consumed by `ib-web-render` for that session's SSE stream rather than by `ib-discord-send`.

### Token minting (`$web`)

The `$web` command becomes a `MINT_LOGIN_TOKEN` envelope. Only `ib-apply` can write to `_sqlweblogintoken`. The minted URL is sent back through the normal reply path → `ib-discord-send` → DM. The token never crosses any process that doesn't strictly need it.

### Read paths (tracker render, character lookup)

Reads bypass the queue entirely. `ib-web-render` (user `ibwww`) opens SQLite read-only. State-change wakeups still come over UDP datagrams (or, more in keeping with the qmail spirit, by tailing a `queue/replies/` subdirectory with inotify), so `ib-web-render` knows when to push an SSE update.

### Vulnerability scan

1. `ib-osv-fetch` (user `ibnet`) makes the outbound HTTPS calls. It writes raw OSV JSON to a pipe.
2. `ib-vuln-process` (user `ibvuln`, no network capability) parses the JSON. If a high-severity finding affects a known dependency, it produces a `POST_VULN_ALERT` envelope and pipes it to `ib-queue` like any other command.
3. `ib-apply` records the alert (de-dup by ID); `ib-discord-send` posts to the alert channel.

A compromise of `ib-osv-fetch` — the most plausible attack path because it talks to an external service — gives the attacker no DB access, no Discord credentials, and no ability to inject arbitrary commands (the `ib-vuln-process` schema is strict).

## Security guarantees

Concretely, what each compromise yields:

- **`ib-discord-recv` compromised** (most exposed surface — parses arbitrary user text): attacker gets Discord read-side token, can read messages the bot can read, **cannot** write to DB, **cannot** post as the bot, **cannot** mint web tokens. Can attempt to inject malformed envelopes into `ib-queue`, but `ib-queue` re-validates schema.
- **`ib-web-recv` compromised**: gets nothing privileged. Read-only DB. Cannot mint tokens. Cannot post to Discord.
- **`ib-queue` compromised**: can write any well-formed envelope, but the envelope grammar is fixed and `ib-apply` enforces all semantic rules (e.g. a player can only modify their own characters). No network, no secrets.
- **`ib-apply` compromised**: can corrupt the DB freely, but has **no** network and **no** access to the Discord token. Exfiltration requires going through the reply queue, which is shaped by reply schema and consumed only by sender processes.
- **`ib-discord-send` compromised**: can post anything to Discord using the write token. **Cannot** read the DB. Cannot mint tokens. The damage is bounded to "messages from the bot user" — which is precisely what the Discord ToS contemplates.
- **`ib-osv-fetch` compromised**: gets the public OSV API. Nothing else.
- **`ib-web-render` compromised**: read-only DB; can serve malicious HTML to clients (XSS-equivalent). Cannot mutate state. Cannot post to Discord.

The Discord write token, the SQLite write capability, and the user-facing input parsers are now in three disjoint processes. There is no single component whose compromise yields the whole system — which is the qmail security property.

Additional structural wins:
- **No untrusted parser ever holds a credential.** OSV JSON parsing happens in a no-network process; Discord gateway parsing happens in a no-DB process.
- **The TCB is small.** `ib-queue` is the closest thing to a privileged choke point and can plausibly be kept under ~300 lines.
- **Schema-enforced command grammar.** SQL injection becomes a structurally weaker threat: input parsers don't construct SQL; they construct envelopes that `ib-apply` translates.

## Reliability guarantees

- **No command loss.** A 2xx-equivalent ack is only returned after `fsync(tmp) + rename + fsync(dir)`. A crash before ack means the user retries; a crash after ack means the queue replays on restart.
- **Crash atomicity.** The queue is a strictly append-by-rename structure. No partial writes are visible. SQLite WAL provides the same property at the storage layer.
- **Workers are restartable.** Any of `ib-apply`, `ib-discord-send`, `ib-web-render`, `ib-osv-fetch` can be SIGKILLed; `ib-send` requeues. The queue is the source of truth.
- **Backpressure is observable.** Queue depth is just `ls queue/todo | wc -l`. `ib-discord-recv` can refuse new commands above a threshold instead of silently absorbing them.
- **Bounded retries.** Outbound failures (Discord 5xx, OSV timeout) follow exponential backoff with explicit eventual-bounce — never silent drops.
- **Single-writer simplicity.** Only one process writes to SQLite, removing an entire class of concurrency bugs even though SQLite WAL would technically allow multiple writers.

## Cost and proportionality

For a Discord bot tracking initiative for a tabletop RPG, this is wildly disproportionate. Honest accounting:

- 8 binaries instead of 2; each needs an entry point, packaging, supervision config (s6/runit/systemd).
- Per-component user accounts and filesystem permissions managed by an installer.
- Operational debugging is harder: a failure is now spread across a chain of processes and a queue.
- Latency increases (probably 10–50 ms per command) — imperceptible for chat, but real.
- The codebase grows ~2–3× from glue.

Where the design genuinely earns its keep:

1. **Splitting the Discord token holder from the Discord input parser.** This alone eliminates the worst single-process compromise. It is achievable with two processes plus a tiny IPC and is probably the highest-leverage piece.
2. **Moving OSV fetch+parse out of the main processes.** Cheap to do, removes external-data parsing from credential-holding code.
3. **An atomic command queue.** Useful even within a single process: replaces direct DB writes with a "queue then apply" pattern that gives crash safety and a clean acceptance contract.

The full eight-process decomposition is interesting as a thought experiment and as a teaching artefact, but for initbot's threat model the staged subset (1)+(2)+(3) captures most of the security benefit at maybe 1.3× the current complexity.

## Files that would be affected if executed

(Sketch only — not for execution in this turn.)

- New package `packages/initbot-queue/` — the envelope schema, `ib-queue`, `ib-send` skeleton.
- Split `packages/initbot-chat/src/initbot_chat/bot.py` into `recv.py` (gateway-only) and `send.py` (post-only).
- Split DB writes out of `packages/initbot-core/src/initbot_core/state/sql.py` into a write-only `apply` entry point; keep read methods callable from `ibwww`.
- Move `packages/initbot-core/src/initbot_core/security.py` into a new `initbot-osv` package, splitting fetch and process.
- Replace `notify.py` UDP signalling with reply-file inotify (or keep UDP as a wakeup hint).
- Containerisation: one image per component, or a single image with multiple ENTRYPOINT-selectable binaries; `tools/set_up_systemd.sh` extended to install per-user services.

## Verification

This is a design document, so verification is conversational rather than executable:

- Walk through each compromise scenario in the "Security guarantees" section and confirm the claimed bounds match the proposed user/permission layout.
- For each data flow, trace the file/socket path from input to durable commit and confirm the acceptance point is past `fsync + rename`.
- Sanity-check the cost section against your appetite — if the answer is "not worth it for a hobby bot", the staged subset (token-holder split + OSV split + atomic queue) is the recommended landing point.
