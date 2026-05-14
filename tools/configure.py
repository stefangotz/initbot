#!/usr/bin/env -S uv run
# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# /// script
# requires-python = ">=3.11"
# ///

"""Interactive setup wizard for initbot.

Guides new users through Discord bot token setup, web app deployment mode
selection, and writing the necessary .env files.

Usage:
    sh ./tools/configure.sh
    uv run tools/configure.py
"""

import getpass
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
    mode: int = 1  # 1=local, 2=own domain, 3=ngrok
    domain: str = ""
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


def _configure_token() -> str:
    print("[1/3] Discord bot token")
    current = read_env(_ENV_CHAT_FILE).get("token", "")
    print(f"  Current: {_mask(current) if current else 'not set'}")
    token = _prompt(
        "  Token (Enter to keep current)" if current else "  Token",
        default=current,
        secret=True,
    )
    if not token:
        print("\nError: a Discord bot token is required.")
        print(f"See {_DISCORD_SETUP_GUIDE} for step-by-step instructions.")
        sys.exit(1)
    return token


def _configure_ngrok(current_domain: str) -> tuple[str, str]:
    """Configure ngrok and return (domain, authtoken)."""
    ngrok = shutil.which("ngrok")
    if not ngrok:
        print("\nError: ngrok is not installed.")
        print(f"Install it from: {_NGROK_INSTALL_URL}")
        print("\nAlternative — Cloudflare Tunnel (free, no session limits):")
        print(f"  {_CLOUDFLARE_TUNNEL_URL}")
        sys.exit(1)

    check = subprocess.run([ngrok, "config", "check"], capture_output=True)  # noqa: S603
    current_authtoken = read_env(_ENV_FILE).get("NGROK_AUTHTOKEN", "")

    print("\n  ngrok authtoken — used for both standalone and Docker Compose.")
    print(
        "  https://dashboard.ngrok.com/get-started/your-authtoken"
    )  # pragma: allowlist secret
    authtoken = _prompt(
        "  ngrok authtoken", default=current_authtoken, secret=True
    )  # pragma: allowlist secret
    if not authtoken:
        print("Error: ngrok authtoken is required.")
        sys.exit(1)

    if check.returncode != 0:
        subprocess.run(  # noqa: S603  user is providing their own authtoken
            [ngrok, "config", "add-authtoken", authtoken],  # pragma: allowlist secret
            check=True,
        )

    print("\n  A free ngrok account gives you one static domain.")
    print(f"  Find it at: {_NGROK_DOMAINS_URL}")
    print(
        f"  (Cloudflare Tunnel is an alternative with no session limits:\n"
        f"   {_CLOUDFLARE_TUNNEL_URL})"
    )
    domain = _prompt(
        "  ngrok static domain (e.g. foo-bar.ngrok-free.app)", default=current_domain
    )
    if not domain:
        print("Error: a domain is required for ngrok mode.")
        sys.exit(1)
    return domain, authtoken


def _configure_web() -> _WebConfig:
    print("\n[2/3] Web app")
    if _prompt("  Enable the web initiative tracker?", default="Y").lower() not in (
        "y",
        "yes",
    ):
        return _WebConfig(enabled=False)

    shared = read_env(_ENV_FILE)
    current_domain = shared.get("DOMAIN", "")
    current_prefix = shared.get("web_url_path_prefix", "")

    print("\n  Deployment mode:")
    print("    1) Local only  — localhost access; $web command unavailable")
    print("    2) Own domain  — Docker Compose + Caddy (requires a public domain)")
    print(
        "    3) ngrok       — free public HTTPS tunnel, no domain required (recommended)"
    )
    mode_raw = _prompt("  Choose mode", default="3")
    mode = int(mode_raw) if mode_raw in ("1", "2", "3") else 3

    prefix = current_prefix or generate_prefix()

    if mode == 1:
        return _WebConfig(enabled=True, mode=1, domain="", prefix=prefix)

    if mode == 2:
        domain = _prompt("  Domain name (e.g. example.com)", default=current_domain)
        if not domain:
            print("Error: a domain name is required.")
            sys.exit(1)
        return _WebConfig(enabled=True, mode=2, domain=domain, prefix=prefix)

    # mode == 3: ngrok
    domain, authtoken = _configure_ngrok(current_domain)
    return _WebConfig(
        enabled=True, mode=3, domain=domain, prefix=prefix, ngrok_authtoken=authtoken
    )


def _write_config(token: str, web: _WebConfig) -> None:
    print("\n[3/3] Summary")

    env_updates: dict[str, str] = {}
    if web.enabled:
        if web.domain:
            env_updates["DOMAIN"] = web.domain
        if web.ngrok_authtoken:
            env_updates["NGROK_AUTHTOKEN"] = (
                web.ngrok_authtoken
            )  # pragma: allowlist secret
        if web.prefix:
            env_updates["web_url_path_prefix"] = web.prefix

    chat_updates: dict[str, str] = {"token": token}  # pragma: allowlist secret

    if env_updates:
        print("\n  .env:")
        for k, v in env_updates.items():
            masked = k in ("NGROK_AUTHTOKEN",)
            print(f"    {k} = {_mask(v) if masked else v}")
    print("\n  .env.chat:")
    print(f"    token = {_mask(token)}")

    if _prompt("\nWrite these settings?", default="Y").lower() not in ("y", "yes"):
        print("Aborted. No files written.")
        sys.exit(0)

    if env_updates:
        update_env(_ENV_FILE, env_updates)
        print("  Written: .env")
    update_env(_ENV_CHAT_FILE, chat_updates)
    print("  Written: .env.chat")


def _print_next_steps(web: _WebConfig) -> None:
    print("\n=== Setup complete! ===\n")
    print("Start the chat bot:")
    print("  sh ./tools/run_chat.sh\n")

    if not web.enabled:
        return

    if web.mode == 1:
        print("Start the web tracker (local access):")
        print("  sh ./tools/run_web_standalone.sh")
    elif web.mode == 2:
        print("Start everything with Docker Compose:")
        print("  sh ./tools/run_compose.sh")
    else:
        print("Start the web tracker with ngrok:")
        print("  sh ./tools/run_web_ngrok.sh      (standalone)")
        print("  sh ./tools/run_compose.sh         (Docker Compose)")


def main() -> None:
    """Run the initbot interactive setup wizard."""
    print("=== Initbot Setup ===\n")
    token = _configure_token()
    web = _configure_web()
    _write_config(token, web)
    _print_next_steps(web)


if __name__ == "__main__":
    main()
