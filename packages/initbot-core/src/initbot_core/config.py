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


CORE_CFG = CoreSettings()
