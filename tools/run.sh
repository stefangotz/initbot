#!/bin/sh

# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

set -ue

REPO_DIR="$(cd "$(dirname "$(realpath "${0}")")"/.. && pwd)"
HOST_LOCK_FILE="${REPO_DIR}/uv.lock"
# This path needs to align with the path set in compose.yml
OUTPUT_LOCK_FILE="${REPO_DIR}/uv.lock.out"

cd "${REPO_DIR}"

if [ -s "${OUTPUT_LOCK_FILE}" ] && [ -f "${HOST_LOCK_FILE}" ]; then
    if [ "$(stat -f '%m' "${OUTPUT_LOCK_FILE}" 2>/dev/null || echo 0)" -gt "$(stat -f '%m' "${HOST_LOCK_FILE}" 2>/dev/null || echo 0)" ]; then
        cp "${OUTPUT_LOCK_FILE}" "${HOST_LOCK_FILE}"
        rm "${OUTPUT_LOCK_FILE}"
    fi
fi

# Ensure that this file exists.
# Otherwise, docker compose up fails because it is not able to bind-mount the file into the auto-remediation container (see compose.yml)
touch -d 1970-01-01T00:00:00Z "${OUTPUT_LOCK_FILE}"

exec docker compose up --build "$@"
