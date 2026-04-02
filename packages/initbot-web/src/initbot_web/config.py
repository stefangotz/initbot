# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

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
    web_host: str = Field(
        default="127.0.0.1",
        description="Host address for the web server to bind to.",
    )
    web_port: int = Field(
        default=8080,
        description="The port the web app listens on.",
    )
