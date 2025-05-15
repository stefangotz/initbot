# Copyright 2021 Stefan Götz <github.nooneelse@spamgourmet.com>

# This file is part of initbot.

# initbot is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.

# initbot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU Affero General Public
# License along with initbot. If not, see <https://www.gnu.org/licenses/>.

from getpass import getpass

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
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


CFG = Settings(_env_file=".env", _env_file_encoding="utf-8", _cli_parse_args=True)  # type: ignore
if not CFG.token:
    CFG.token = getpass(
        "Please enter your Discord bot token (you can also supply it as a command line argument, an environment variable, or through a .env file): "
    )
