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

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    project_name: str = "initbot"
    project_description: str = "A Discord bot that manages RPG character initiatives"
    project_license: str = """initbot is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of
the License, or (at your option) any later version.

initbot is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU Affero General Public
License along with initbot. If not, see <https://www.gnu.org/licenses/>."""
    project_version: str = "0.1.0"
    token: str = ""
    appId: str = ""
    botlink: str = ""
    # To specify multiple command prefixes, separate them with a comma.
    # For example: command_prefixes: str = "$,!"
    command_prefixes: str = "$"
    # Configures the data store that contains the bot state.
    # The default is "json:./" which maintains the state as a set of JSON files in the current working directory.
    state: str = "json:./"


CFG = Settings(_env_file=".env", _env_file_encoding="utf-8") if Path(".env").exists() else Settings()  # type: ignore
if not CFG.token:
    raise ValueError(
        "The Discord bot token is not set. Without a token, the bot is not able to authenticate. Configure the token via the environment variable TOKEN or via a '.env' file."
    )
