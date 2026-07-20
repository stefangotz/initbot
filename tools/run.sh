#!/bin/sh

# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

set -ue

REPO_DIR="$(cd "$(dirname "$(realpath "${0}")")"/.. && pwd)"
HOST_LOCK_FILE="${REPO_DIR}/uv.lock"
AUTO_REMEDIATED_LOCK_FILE="${REPO_DIR}/uv.lock-auto-remediated"

cd "${REPO_DIR}"

if [ -s "${AUTO_REMEDIATED_LOCK_FILE}" ] && [ -f "${HOST_LOCK_FILE}" ]; then
    if [ "$(stat -f '%m' "${AUTO_REMEDIATED_LOCK_FILE}" 2>/dev/null || echo 0)" -gt "$(stat -f '%m' "${HOST_LOCK_FILE}" 2>/dev/null || echo 0)" ]; then
        cp "${AUTO_REMEDIATED_LOCK_FILE}" "${HOST_LOCK_FILE}"
        rm "${AUTO_REMEDIATED_LOCK_FILE}"
        touch -d 1970-01-01T00:00:00Z "${AUTO_REMEDIATED_LOCK_FILE}"
    fi
fi

exec docker compose up --build "$@"
