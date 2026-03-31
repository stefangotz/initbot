# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from pathlib import Path


def check_state_directory(state_uri: str, directory: Path) -> None:
    """Exit with a clear message if *directory* does not exist.

    Args:
        state_uri: The full STATE config value (e.g. 'sqlite:/data/app.sqlite').
        directory: The directory that must exist before the store can be used.
    """
    if not directory.exists():
        raise SystemExit(
            f"State directory does not exist: {str(directory)!r}\n"
            f"  Configured STATE: {state_uri!r}\n"
            f"  Create the directory or update the state configuration option or STATE environment variable to point to an existing location."
        )
