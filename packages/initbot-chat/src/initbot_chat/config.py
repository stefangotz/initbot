# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from getpass import getpass

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"extra": "ignore"}

    token: str = Field(
        default="",
        description="The Discord bot token. This is required to authenticate the bot with Discord. There are a lot of online resources on how to create a bot token.",
    )
    command_prefixes: str = Field(
        default="$",
        description="The bot only recognizes commands with one of the prefixes in this comma-separated list. Note that the empty string is a valid prefix, so if you want to use the bot without a command prefix, set this to an empty string.",
    )
    state: str = Field(
        default="json:./",
        description="The data store that contains the bot state. This is a URI that specifies the type of data store and the location of the data store. The default is 'json:./' which maintains the state as a set of JSON files in the current working directory.",
    )
    max_inline_roll_message_length: int = Field(
        default=90,
        description="Messages longer than this number of characters will not have dice roll expressions expanded inline. This prevents the bot from expanding dice-roll-like expressions in longer, non-game messages.",
    )
    alert_channel_id: str = Field(
        default="",
        description=(
            "The numeric ID of the Discord channel where security vulnerability alerts are posted. "
            "When not set, vulnerability checks run and findings are logged, but no channel alert is sent. "
            "To find a channel ID in Discord: enable Developer Mode under User Settings → Advanced, "
            "then right-click the desired channel and select 'Copy Channel ID'."
        ),
    )


CFG = Settings(
    _env_file=[".env", ".env.chat"],  # type: ignore[unknown-argument]
    _env_file_encoding="utf-8",  # type: ignore[unknown-argument]
    _cli_parse_args=True,  # type: ignore[unknown-argument]
)
if not CFG.token:
    CFG.token = getpass(
        "Please enter your Discord bot token (you can also supply it as a command line argument, an environment variable, or through a .env file): "
    )
