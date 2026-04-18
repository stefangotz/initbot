#!/bin/sh

# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

set -ue

# shellcheck source=tools/uv_version.sh
. "$(dirname "$0")/uv_version.sh"

if ! command -v uv > /dev/null 2>&1; then
    OS=$(uname -s)
    ARCH=$(uname -m)

    case "${OS}-${ARCH}" in
        Darwin-arm64)
            TARBALL="uv-aarch64-apple-darwin.tar.gz"
            SHA256="${UV_SHA256_DARWIN_ARM64}"
            ;;
        Darwin-x86_64)
            TARBALL="uv-x86_64-apple-darwin.tar.gz"
            SHA256="${UV_SHA256_DARWIN_X86_64}"
            ;;
        Linux-x86_64)
            TARBALL="uv-x86_64-unknown-linux-gnu.tar.gz"
            SHA256="${UV_SHA256_LINUX_X86_64}"
            ;;
        Linux-aarch64)
            TARBALL="uv-aarch64-unknown-linux-gnu.tar.gz"
            SHA256="${UV_SHA256_LINUX_AARCH64}"
            ;;
        *)
            echo "Unsupported platform: ${OS}-${ARCH}" >&2
            exit 1
            ;;
    esac

    TMP_DIR=$(mktemp -d)
    trap 'rm -rf "$TMP_DIR"' EXIT

    curl -LsSf -o "${TMP_DIR}/${TARBALL}" \
        "https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/${TARBALL}"

    if command -v sha256sum > /dev/null 2>&1; then
        echo "${SHA256}  ${TMP_DIR}/${TARBALL}" | sha256sum -c -
    else
        echo "${SHA256}  ${TMP_DIR}/${TARBALL}" | shasum -a 256 -c -
    fi

    TAR_DIR="${TARBALL%.tar.gz}"
    tar -xzf "${TMP_DIR}/${TARBALL}" -C "${TMP_DIR}"
    mkdir -p "${HOME}/.local/bin"
    mv "${TMP_DIR}/${TAR_DIR}/uv" "${HOME}/.local/bin/uv"
fi
