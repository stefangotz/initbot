#!/usr/bin/env -S uv run
# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# /// script
# requires-python = ">=3.11"
# ///

"""Interactive setup wizard for initbot.

Guides new admins through application selection, credential setup, and
deployment mode configuration. Writes the .env files that docker compose reads.

Usage:
    ./tools/configure.sh
"""

import getpass
import re
import secrets
import shutil
import string
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Final

_REPO_ROOT: Final[Path] = Path(__file__).resolve().parent.parent
_ENV_FILE: Final[Path] = _REPO_ROOT / ".env"
_ENV_CHAT_FILE: Final[Path] = _REPO_ROOT / ".env.chat"

_ALPHABET: Final[str] = string.ascii_letters + string.digits
_PREFIX_LENGTH: Final[int] = 40

# ngrok auth tokens are long alphanumeric strings (40+ characters).
# This pattern rejects obviously wrong values such as Cloudflare tokens (cr_…).
_NGROK_AUTHTOKEN_RE: Final[re.Pattern[str]] = re.compile(r"^[a-zA-Z0-9_]{40,}$")

_NGROK_INSTALL_URL: Final[str] = "https://ngrok.com/download"
_NGROK_DOMAINS_URL: Final[str] = "https://dashboard.ngrok.com/domains"
_CLOUDFLARE_TUNNEL_URL: Final[str] = (
    "https://developers.cloudflare.com/cloudflare-one/connections/"
    "connect-networks/get-started/"
)
_DISCORD_SETUP_GUIDE: Final[str] = "docs/discord-bot-setup.md"


@dataclass
class _WebConfig:
    enabled: bool = False
    mode: int = 1  # 1=local, 2=ngrok, 3=webserver
    web_hostname: str = ""
    prefix: str = ""
    ngrok_authtoken: str = ""


def read_env(path: Path) -> dict[str, str]:
    """Read a .env file and return a dict of unquoted key-value pairs.

    Args:
        path: Path to the .env file.

    Returns:
        Dict of key-value pairs. Empty dict if the file does not exist.
    """
    if not path.exists():
        return {}
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        result[key] = value
    return result


def update_env(path: Path, updates: dict[str, str]) -> None:
    """Update or append keys in a .env file, preserving all other content.

    Performs an atomic write via a temporary file in the same directory.
    Values containing spaces are written with double quotes; others are unquoted.

    Args:
        path: Path to the .env file (created if absent).
        updates: Keys to set. Existing keys are updated in-place; new keys are appended.
    """
    existing_lines: list[str] = (
        path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    )
    updated_keys: set[str] = set()
    new_lines: list[str] = []

    for line in existing_lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key, _, _ = stripped.partition("=")
            key = key.strip()
            if key in updates:
                value = updates[key]
                new_lines.append(
                    f'{key}="{value}"' if " " in value else f"{key}={value}"
                )
                updated_keys.add(key)
                continue
        new_lines.append(line)

    for key, value in updates.items():
        if key not in updated_keys:
            new_lines.append(f'{key}="{value}"' if " " in value else f"{key}={value}")

    content = "\n".join(new_lines)
    if new_lines:
        content += "\n"

    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp"
    ) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    tmp_path.rename(path)


def generate_prefix() -> str:
    """Generate a 40-character cryptographically random alphanumeric URL prefix."""
    return "".join(secrets.choice(_ALPHABET) for _ in range(_PREFIX_LENGTH))


def _prompt(question: str, default: str = "", secret: bool = False) -> str:
    hint = (" [keep current]" if secret else f" [{default}]") if default else ""
    full_prompt = f"{question}{hint}: "
    raw = getpass.getpass(full_prompt) if secret else input(full_prompt)
    return raw.strip() or default


def _mask(token: str) -> str:
    return f"...{token[-6:]}" if len(token) >= 6 else "***"


def _choose_applications() -> tuple[bool, bool]:
    """Ask what to run. Returns (run_bot, run_web)."""
    print("What do you want to run?")
    print("  1) Chat bot only")
    print("  2) Web tracker only")
    print("  3) Both")
    while True:
        choice = _prompt("Choose", default="3")
        if choice == "1":
            return True, False
        if choice == "2":
            return False, True
        if choice == "3":
            return True, True
        print("  Please enter 1, 2, or 3.")


def _configure_token() -> str:
    """Ask for and return a non-empty Discord bot token."""
    current = read_env(_ENV_CHAT_FILE).get("token", "")
    if current:
        print(f"  Current token: {_mask(current)}")
    else:
        print(
            f"  You need a Discord bot token. See {_DISCORD_SETUP_GUIDE} for instructions."
        )
    label = "  Token (Enter to keep current)" if current else "  Token"
    token = _prompt(label, default=current, secret=True)
    if not token:
        print("\nError: a Discord bot token is required.")
        sys.exit(1)
    return token


def _choose_web_mode() -> int:
    """Ask for the web deployment mode. Re-prompts if ngrok is chosen but not installed."""
    while True:
        print("\n  Deployment mode:")
        print(
            "    1) Local mode      — only accessible on this computer; no internet required"
        )
        print(
            "    2) ngrok mode      — players connect from anywhere; requires a free ngrok account"
        )
        print(
            "    3) Webserver mode  — players connect from anywhere; requires a public web address"
        )
        mode_raw = _prompt("  Choose", default="2")
        if mode_raw not in ("1", "2", "3"):
            print("  Please enter 1, 2, or 3.")
            continue
        mode = int(mode_raw)
        if mode == 2 and not shutil.which("ngrok"):
            print(
                "\n  ngrok is not installed. Download and install it, then re-run configure.sh,"
            )
            print("  or choose a different mode.")
            print(f"\n  Download ngrok: {_NGROK_INSTALL_URL}")
            continue
        return mode


def _configure_ngrok(current_hostname: str) -> tuple[str, str]:
    """Configure ngrok credentials and optional static hostname. Returns (hostname, authtoken)."""
    ngrok = shutil.which("ngrok")
    if not ngrok:
        raise RuntimeError("ngrok not found; _choose_web_mode should have caught this")
    check = subprocess.run([ngrok, "config", "check"], capture_output=True)  # noqa: S603
    current_authtoken = read_env(_ENV_FILE).get("NGROK_AUTHTOKEN", "")

    print("\n  ngrok auth token")
    print(
        "  https://dashboard.ngrok.com/get-started/your-authtoken"
    )  # pragma: allowlist secret
    while True:
        authtoken = _prompt(
            "  Auth token", default=current_authtoken, secret=True
        )  # pragma: allowlist secret
        if not authtoken:
            print("  An ngrok auth token is required.")
            continue
        if _NGROK_AUTHTOKEN_RE.match(authtoken):
            break
        print("  That doesn't look like a valid ngrok auth token.")
        print(
            "  Tokens are long strings of letters, numbers, and underscores (40+ characters)."
        )
        print(
            "  Make sure you copied it from your ngrok dashboard, not from another service."
        )
        current_authtoken = ""  # don't re-offer the invalid value as default

    if check.returncode != 0:
        subprocess.run(  # noqa: S603  user is providing their own authtoken
            [ngrok, "config", "add-authtoken", authtoken],  # pragma: allowlist secret
            check=True,
        )

    print("\n  Fixed web address (optional but recommended):")
    print(
        "  A fixed address keeps the join link stable — players use the same link every time."
    )
    print("  Without one, the address changes each time initbot restarts.")
    print(f"  Find your free fixed address at: {_NGROK_DOMAINS_URL}")
    hostname = _prompt(
        "  Fixed address (leave blank for a random address each restart)",
        default=current_hostname,
    )
    return hostname, authtoken


def _configure_web() -> _WebConfig:
    """Configure the web tracker. Returns a fully populated _WebConfig."""
    shared = read_env(_ENV_FILE)
    current_hostname = shared.get("WEB_HOSTNAME", "")
    current_prefix = shared.get("web_url_path_prefix", "")
    prefix = current_prefix or generate_prefix()

    mode = _choose_web_mode()

    if mode == 1:
        return _WebConfig(enabled=True, mode=1, web_hostname="", prefix=prefix)

    if mode == 3:
        print("\n  Enter the web address players will use to reach this server.")
        print("  You need a DNS record pointing that address at this machine.")
        hostname = _prompt(
            "  Web address (e.g. example.com)",
            default=current_hostname,
        )
        if not hostname:
            print("Error: a public hostname is required.")
            sys.exit(1)
        return _WebConfig(enabled=True, mode=3, web_hostname=hostname, prefix=prefix)

    # mode == 2: ngrok
    hostname, authtoken = _configure_ngrok(current_hostname)
    return _WebConfig(
        enabled=True,
        mode=2,
        web_hostname=hostname,
        prefix=prefix,
        ngrok_authtoken=authtoken,
    )


def _write_config(token: str | None, web: _WebConfig) -> None:
    """Show a plain-language summary, confirm, and write configuration files."""
    print("\n=== Summary ===\n")
    print(f"  Chat bot:    {'enabled' if token is not None else 'off'}")
    if web.enabled:
        mode_label = {1: "local mode", 2: "ngrok mode", 3: "webserver mode"}[web.mode]
        print(f"  Web tracker: {mode_label}")
        if web.mode == 1:
            print("               address: http://localhost:8080")
        elif web.mode == 2:
            if web.web_hostname:
                print(f"               address: https://{web.web_hostname}")
            else:
                print("               address: random (changes each restart)")
        else:
            print(f"               address: https://{web.web_hostname}")
    else:
        print("  Web tracker: off")

    if _prompt("\n  Save configuration?", default="Y").lower() not in ("y", "yes"):
        print("Aborted. No files written.")
        sys.exit(0)

    profiles: list[str] = []
    if token:
        profiles.append("chat")
    if web.enabled:
        profiles.append("web")
        if web.mode == 2:
            profiles.append("ngrok")
        elif web.mode == 3:
            profiles.append("caddy")

    env_updates: dict[str, str] = {"COMPOSE_PROFILES": ",".join(profiles)}
    if web.enabled:
        env_updates["WEB_HOSTNAME"] = web.web_hostname
        if web.ngrok_authtoken:
            env_updates["NGROK_AUTHTOKEN"] = (
                web.ngrok_authtoken
            )  # pragma: allowlist secret
        if web.prefix:
            env_updates["web_url_path_prefix"] = web.prefix

    update_env(_ENV_FILE, env_updates)
    if token is not None:
        update_env(_ENV_CHAT_FILE, {"token": token})  # pragma: allowlist secret
    print("  Configuration saved.")


def _print_next_steps() -> None:
    print("\n=== Setup complete! ===\n")
    print("Start initbot:")
    print("  ./tools/run.sh")


def main() -> None:
    """Run the initbot interactive setup wizard."""
    print("=== Initbot Setup ===\n")
    print("This wizard sets up initbot. It will ask what you want to run and how.\n")

    run_bot, run_web = _choose_applications()

    token: str | None = None
    if run_bot:
        print("\n--- Chat bot ---")
        token = _configure_token()

    web = _WebConfig(enabled=False)
    if run_web:
        print("\n--- Web tracker ---")
        web = _configure_web()

    _write_config(token, web)
    _print_next_steps()


if __name__ == "__main__":
    main()
