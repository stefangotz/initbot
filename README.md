# Initbot

Discord bot that manages RPG character initiatives

## Discord

The bot understands a few commands.
These can be sent in any channel the bot user is a member of or as DMs.
Simply type `$help` to see what the bot can do for you.

### Initiative

The typical flow during a game session is:

1. The Judge declares initiative to be rolled
2. Player A rolls an initiative value of 10 and types `$init Alfalfa 10` to create their character *Alfalfa* (if it doesn't exist yet) and set their initiative to 10.
3. All other players do the same for their characters and the Judge for all NPCs.
4. The Judge types `$inis` to obtain all characters and NPCs in initiative order.
5. Departed characters and NPCs can be removed with, e.g., `$remove Alfalfa` at any time.

Note that anyone (i.e., any Discord user on a given server) can update the initiative of or remove the character of any other player.

Get more information on any of the commands with `$help`, e.g., `$help init`.

## Development

To get started on Linux or MacOS and set up everything you need for initbot development, run `./tools/setup.sh`.
That script boils down to:

- setting up `uv`
- setting up a Python virtual environment
- setting up pre-commit hooks

On Windows, the script won't run as such, but the commands it contains should translate quite easily.

## Running initbot

To run the bot straight from the repository:

- create a Discord bot token (see Google)
- run `./tools/setup.sh` (or make sure you have `uv` and run `uv sync`)
- run `./tools/run.sh` (or the commands that script contains)

### Configuration

Without configuration, the bot interactively prompts for any parameter it requires to run.
However, that can be become tedious, so there are three ways to provide configuration parameters:

- command line options: `./tools/run.sh --token 123`
- environment variables: `export token=123; ./tools/run.sh`
- a `.env` file with `token=123`

The bot currently supports the configuration parameters listed in [`initbot/bot/config.py`](initbot/bot/config.py) .
You can also run `./tools/run.sh --help` for the same information.

### Containers

To run initbot in a docker container:

- build the image with `docker build -t initbot .`
- run initbot
  - without configuration: `docker run -it initbot`
  - with command line arguments: `docker run initbot --token 123`
  - with a `.env` file containing `token=123`: `docker run --env-file .env initbot`
