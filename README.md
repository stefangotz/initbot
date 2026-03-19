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

The web app reflects some of the same information as the chat bot, just in a browser.
It can access the same data source as the chat bot, so both applications can interact.

## Development

To get started on Linux or MacOS and set up everything you need for development, run `./tools/setup.sh`.
That script boils down to:

- setting up `uv`
- setting up a Python virtual environment
- setting up pre-commit hooks

On Windows, the script won't run as such, but the commands it contains should translate quite easily.

## Running the applications

### Chat bot

To run the chat bot straight from the repository:

- create a Discord bot token (see Google)
- run `./tools/setup.sh` (or make sure you have `uv` and run `uv sync`)
- run `./tools/run_chat.sh` (or the commands that script contains)

### Web app

- run `./tools/run_web.sh` (or the commands that script contains)

### Configuration

Configuration is loaded from layered `.env` files. Each app reads the shared
`.env` first, then its own app-specific file (which takes precedence):

| File | Used by | Typical contents |
| --- | --- | --- |
| `.env` | both | `state=` (SQLite URI) |
| `.env.chat` | initbot-chat | `token=`, `command_prefixes=` |
| `.env.web` | initbot-web | `web_secret=`, `web_port=` |

In addition to `.env` files, parameters can be supplied via:

- command line options: `./tools/run_chat.sh --token 123`
- environment variables: `export token=123; ./tools/run_chat.sh`

Supported parameters are listed in
[`packages/initbot-chat/src/initbot_chat/config.py`](packages/initbot-chat/src/initbot_chat/config.py)
and
[`packages/initbot-web/src/initbot_web/config.py`](packages/initbot-web/src/initbot_web/config.py).
You can also run `./tools/run_chat.sh --help` or `./tools/run_web.sh --help`.

### Containers

The repository ships two Docker images built from the same `Dockerfile`:

| Target | Image | Entrypoint |
| --- | --- | --- |
| `chat` | `initbot-chat` | `/app/bin/initbot` |
| `web` | `initbot-web` | `/app/bin/initbot-web` |

Build them individually:

```sh
docker build --target chat -t initbot-chat .
docker build --target web  -t initbot-web  .
```

Or use Docker Compose to build and run both together with a shared SQLite volume:

```sh
docker compose up --build
```

The compose file mounts a named volume `data` at `/data` in both containers and sets `STATE=sqlite:/data/app.sqlite` so they share the same database.
App-specific configuration goes in `.env.chat` (token, prefixes) and `.env.web` (secret, port).
Shared configuration goes in `.env`.
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
