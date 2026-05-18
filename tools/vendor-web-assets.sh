#!/bin/sh

# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# Download and vendor external web assets (Datastar JS + Google Fonts) into the
# package static directory. Idempotent: already-present files are skipped.
# Runs during Docker build (builder stage) and on first dev server start.

set -eu

cd "$(dirname "$(realpath "$0")")"/..

STATIC="packages/initbot-web/src/initbot_web/static"
mkdir -p "$STATIC/fonts"

_fetch() {
    if command -v curl > /dev/null 2>&1; then
        curl -sfL "$1" -o "$2"
    else
        wget -qO "$2" "$1"
    fi
}

_verify_sha256() {
    python3 - "$1" "$2" <<'PYEOF'
import hashlib, sys
expected, path = sys.argv[1], sys.argv[2]
with open(path, "rb") as f:
    actual = hashlib.sha256(f.read()).hexdigest()
if actual != expected:
    print(f"Checksum mismatch for {path}: expected {expected}, got {actual}", file=sys.stderr)
    sys.exit(1)
print(f"{path}: OK")
PYEOF
}

# --- Datastar JS (pinned to v1.0.0-RC.8) ---
if [ ! -f "$STATIC/datastar.js" ]; then
    echo "Downloading Datastar JS..."
    _fetch \
        'https://cdn.jsdelivr.net/gh/starfederation/datastar@v1.0.0-RC.8/bundles/datastar.js' \
        "$STATIC/datastar.js"
    _verify_sha256 \
        'c7f69d2f28ca0d5f4dc9acbdf5cf590bb411d02785c74f86899c611d81c6adcd' `# pragma: allowlist secret` \
        "$STATIC/datastar.js"
fi

# --- Google Fonts: Cinzel 400 + 700 ---
# Uses Python (available in the uv environment and the Alpine builder image) for
# reliable URL extraction and string replacement without non-portable grep -P.
if [ ! -f "$STATIC/fonts.css" ]; then
    echo "Downloading Google Fonts..."
    python3 - "$STATIC" <<'PYEOF'
import sys
import re
import urllib.request

static = sys.argv[1]
ua = "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"
css_url = "https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&display=swap"

req = urllib.request.Request(css_url, headers={"User-Agent": ua})
with urllib.request.urlopen(req) as resp:
    css = resp.read().decode()

seen: dict[str, str] = {}
for font_url in re.findall(r"https://fonts\.gstatic\.com/[^)]+", css):
    if font_url in seen:
        continue
    fname = f"cinzel-{len(seen)}.woff2"
    with urllib.request.urlopen(font_url) as resp:
        with open(f"{static}/fonts/{fname}", "wb") as f:
            f.write(resp.read())
    seen[font_url] = fname

for font_url, fname in seen.items():
    css = css.replace(font_url, f"/static/fonts/{fname}")

with open(f"{static}/fonts.css", "w") as f:
    f.write(css)
PYEOF
fi
