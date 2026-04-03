# Initbot

An RPG Discord chat bot and a companion web app.

## Applications

### initbot-chat — Discord chat bot

The chat bot manages RPG character initiatives.
Commands can be sent in any channel the bot user is a member of or as DMs.
Type `$help` to see what the bot can do for you.

#### Initiative

The typical flow during a game session is:

1. The Judge declares initiative to be rolled
2. Player A rolls an initiative value of 10 and types `$init Alfalfa 10` to create their character *Alfalfa* (if it doesn't exist yet) and set their initiative to 10.
3. All other players do the same for their characters and the Judge for all NPCs.
4. The Judge types `$inis` to obtain all characters and NPCs in initiative order.
5. Departed characters and NPCs can be removed with, e.g., `$remove Alfalfa` at any time.

Note that anyone (i.e., any Discord user on a given server) can update the initiative of or remove the character of any other player.

Get more information on any of the commands with `$help`, e.g., `$help init`.

### initbot-web — companion web app

The web app shows the current initiative order in a live-updating browser view — useful for
displaying on a shared screen or a second monitor during play.

#### Logging in

The web app has no public login page. Players authenticate via a personal, single-use link
delivered by the chat bot:

1. In any channel the bot is in, or in a DM to the bot, type `$web`.
2. The bot sends a private DM with a personal login link. The link expires in one minute and
   can only be used once.
3. Click the link. The browser opens the initiative tracker and stays logged in for eight hours.
   After that, type `$web` again to get a fresh link.

If you type `$web` in a channel rather than in a DM, the bot posts a brief "check your DMs"
notice in the channel that disappears after a few seconds — the actual login link is always
delivered privately.

### Chat bot and web app integration

#### How they are connected

The two applications share a single SQLite database file. They do not communicate directly
with each other over a network. The chat bot writes initiative data and login tokens to the
database; the web app reads from the same database. This keeps the architecture simple and
avoids the need for any additional infrastructure between the two processes.

#### Login flow in detail

When a player runs `$web`:

1. The bot generates a random, single-use token and writes it to the shared database with a
   60-second expiry.
2. The bot constructs a personal login URL — `https://<DOMAIN>/<token>/` — and sends it to
   the player via Discord DM.
3. The player opens the link. The web app looks up the token in the database, verifies it has
   not been used and has not expired, then invalidates it and creates a signed browser session.
4. Subsequent requests carry the session cookie. The session expires after eight hours.

#### Why Discord is the identity provider

The bot already knows who sent the `$web` command — Discord provides the sender's identity
cryptographically. The DM channel is a private channel that only the player and the bot can
see. Together these mean no separate account system, password storage, or OAuth integration
is needed. Discord itself acts as the trusted authentication channel.

#### Security design

All web app endpoints sit under a hard-to-guess URL prefix (`web_url_path_prefix`). This
means the application is invisible to port scanners and opportunistic probes: without knowing
the prefix, there is nothing to attack. Login tokens are single-use and expire in 60 seconds,
so an intercepted link cannot be replayed. Sessions are signed cookies; the signing key is
generated in memory at startup and never written to disk, so there is nothing to steal from
the filesystem.

#### Prerequisites for the web app

For the web app and its login flow to work, operators must ensure:

1. **Shared state.** Both applications must be configured with the same SQLite URI:
   `state=sqlite:/path/to/app.sqlite`. In the Docker Compose setup this is handled
   automatically via a shared named volume.

2. **Public domain.** The `DOMAIN` setting must be set to the publicly reachable domain name
   of the web app (e.g. `example.com`). The bot uses this to construct the login URL it sends
   to players. Without it the `$web` command is not registered and no login links are issued.

3. **URL path prefix.** The `web_url_path_prefix` setting must be set to a stable,
   hard-to-guess value in `.env` or `.env.web` (e.g. a long random string). If it is left
   unset the web app generates a random prefix at startup, but the `$web` command will not be
   registered — the bot only registers the command when both `DOMAIN` and
   `web_url_path_prefix` are explicitly configured. A prefix that changes on every restart
   would also invalidate any bookmarks players have saved.

4. **Discord DM permissions.** The bot must be able to send DMs to players. Some Discord
   server privacy settings allow members to block DMs from other server members, which also
   blocks bot DMs. Players who do not receive the login link should check their Discord
   privacy settings under *Server Privacy Defaults* or *Privacy & Safety*.

## Application Setup & Execution

To run the chat bot application, you first need to [create a Discord bot token](https://duckduckgo.com/?q=how+to+create+a+discord+bot+token).

### Test / One-Off

1. Clone git repository or download repository contents
1. Run chat bot: `sh ./tools/run_chat.sh`
1. Run web app: `sh ./tools/run_web.sh`

### Docker Compose Services

This setup always runs both applications together with a Caddy reverse proxy that serves the web app over HTTPS.

Required configuration:

| File | Setting | Description |
| --- | --- | --- |
| `.env` | `DOMAIN=<your-domain>` | Domain name Caddy uses for TLS and routing |
| `.env.chat` | `token=<discord-bot-token>` | Discord bot token |

Setup steps:

1. Clone git repository or download repository contents
1. Create `.env` with `DOMAIN=<your-domain>` and `.env.chat` with `token=<discord-bot-token>` in the repository
1. Set up a systemd service: `sh ./tools/set_up_systemd.sh compose`
   The script installs the service unit file and prompts whether to enable and start it.

`web_url_path_prefix` is auto-generated if not set.
The web app is reachable at `https://<DOMAIN>/<web_url_path_prefix>/`.

### Configuration

First off, you can run the initbot applications without configuring them ahead of time.
They will simply prompt for required configuration data.

You can run that configuration mode explicitly at any time with the command `sh ./tools/configure.sh`

The initbot applications accept their configuration parameters in any combination of command-line options, environment variables, and `.env` files.

Configuration parameters are loaded from layered `.env` files.
Each app reads the shared `.env` first, then its own app-specific file (which takes precedence):

| File | Used by | Typical contents |
| --- | --- | --- |
| `.env` | both | `state=` (SQLite URI) |
| `.env.chat` | initbot-chat | `token=`, `command_prefixes=` |
| `.env.web` | initbot-web | `web_url_path_prefix=`, `web_port=` |

In addition to `.env` files, parameters can be supplied via:

- command line options: `./tools/run_chat.sh --token 123`
- environment variables: `export token=123; ./tools/run_chat.sh`

Supported parameters are listed in

- [`packages/initbot-core/src/initbot_core/config.py`](packages/initbot-core/src/initbot_core/config.py)
- [`packages/initbot-chat/src/initbot_chat/config.py`](packages/initbot-chat/src/initbot_chat/config.py)
- [`packages/initbot-web/src/initbot_web/config.py`](packages/initbot-web/src/initbot_web/config.py).

You can also run `./tools/run_chat.sh --help` or `./tools/run_web.sh --help`.

### Containers

The repository defines two Docker images built from the same `Dockerfile`:

| Target | Image | Entrypoint |
| --- | --- | --- |
| `chat` | `initbot-chat` | `/app/bin/initbot` |
| `web` | `initbot-web` | `/app/bin/initbot-web` |

Build them individually:

```sh
docker build --target chat -t initbot-chat .
docker build --target web  -t initbot-web  .
```

Or use Docker Compose to build and run both together with a shared volume for state:

```sh
docker compose up --build
```

The compose file mounts a named volume `data` at `/data` in both containers and sets `STATE=sqlite:/data/app.sqlite` so they share the same database.
App-specific configuration goes in `.env.chat` (token, prefixes) and `.env.web` (secret, port).
Shared configuration goes in `.env*` files.
None of these files are required — the compose file won't error if they're absent.

To run a single image manually:

```sh
# Chat bot — interactive (prompts for token if not set)
docker run -it initbot-chat

# Chat bot — with env files
docker run --env-file .env --env-file .env.chat initbot-chat

# Chat bot — with token on the command line and an sqlite datastore in a named docker volume
docker run initbot-chat --token 123 -e STATE=sqlite:/data/app.sqlite -v mydata:/data

# Web app — with an sqlite datastore in a named docker volume
docker run -e STATE=sqlite:/data/app.sqlite -v mydata:/data initbot-web
```

## Development

To get started on Linux or MacOS and set up everything you need for development, run `./tools/set_up_dev.sh`.
That script boils down to:

- setting up `uv`
- setting up a Python virtual environment with the Python dependencies
- setting up pre-commit hooks

On Windows, the script won't run as such, but the commands it contains should translate quite easily.
