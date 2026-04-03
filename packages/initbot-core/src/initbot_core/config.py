# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from pydantic import Field
from pydantic_settings import BaseSettings


class CoreSettings(BaseSettings):
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }
    prune_threshold_days: int = Field(
        default=90,
        description="Characters not used in this many days are eligible for pruning.",
    )
    web_url_path_prefix: str = Field(
        default="",
        description="URL path prefix for the web app. Acts as a hard-to-guess component that obscures well-known endpoints. Auto-generated at startup when unset. Set WEB_URL_PATH_PREFIX in .env for a stable, shareable URL across restarts.",
    )
    domain: str = Field(
        default="",
        description="Public domain name when running behind a reverse proxy (e.g. 'example.com'). Must use uppercase DOMAIN so Caddy picks it up correctly.",
    )


CORE_CFG = CoreSettings()
