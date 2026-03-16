# Copyright 2026 Stefan Götz <github.nooneelse@spamgourmet.com>

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

import secrets

from pydantic import Field
from pydantic_settings import BaseSettings


class WebSettings(BaseSettings):
    model_config = {
        "env_file": [".env", ".env.web"],
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    state: str = Field(
        default="json:./",
        description="The data store that contains the bot state. This is a URI that specifies the type of data store and the location of the data store. The default is 'json:./' which maintains the state as a set of JSON files in the current working directory.",
    )
    web_port: int = Field(
        default=8080,
        description="The port the web app listens on.",
    )
    web_secret: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="The secret path component that protects the web app URL. Defaults to a random token generated at startup.",
    )
