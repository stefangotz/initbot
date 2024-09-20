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

Improvements to the code are most welcome.

To get started with this Python project, note that it relies on a number of fairly common Python tools to improve the development experience, first and foremost being *uv*.
The script `tools/setup.sh` contains the instructions to initialise a development environment for this project.
If on Windows, try running it from a *git bash* session or simply run the commands it contains on the command prompt or a powershell session.

## Running initbot Locally

To run a local instance of the bot straight from the repository:

- create a Discord bot token (see Google)
- create a `.env` file at the top of the repository
- add the line `token=[TOKEN]` with the bot token to the `.env` file
- run `tools/run.sh` (or the commands that script contains)

## Running initbot in a Container

To run initbot in a docker container:

- build the image with `docker build .`
- set up an `.env` file with a Discord bot token as above
- run initbot with `docker run --env-file .env [IMAGE_ID]`
