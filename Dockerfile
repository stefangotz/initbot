# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# Stage 0: pin base images
# The hashes are platform-independent manifest hashes instead of image hashes. Obtain manifest hashes via `docker buildx imagetools inspect IMG_NAME:LABEL`.
FROM ghcr.io/astral-sh/uv:0.13.0-alpine@sha256:20d3fe1308ffa40b51c5c20e002bab5fece40585edcee8ec99357309e8363424 AS uv
FROM python:3.15.0-alpine3.24@sha256:2699b90f4d562a22e2dd076c82f964032f64814204bff36d271a54ba4cc2c7e2 AS python-uv
COPY --from=uv /usr/local/bin/uv* /usr/local/bin/

# Stage 1: build all three wheels
FROM python-uv AS builder
COPY . /root/
WORKDIR /root
RUN tools/vendor-web-assets.sh
RUN --mount=type=cache,target=/root/.cache/uv,sharing=locked \
    uv build --package initbot-core --wheel \
    && uv build --package initbot-chat --wheel \
    && uv build --package initbot-web --wheel

# Stage 2: shared OS configuration (no packages)
# builder and runtime-base are shared layers. Building chat and web in two
# separate `docker buildx build` calls causes a race: the background cache
# export from the first call holds a write lock on these layers when the second
# call starts, failing with a "failed to get lease" error. Use
# `docker buildx bake -f docker-bake.hcl` to build both targets in a single
# BuildKit session, which eliminates the contention.
FROM python-uv AS runtime-base
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN --mount=type=cache,target=/var/cache/apk \
    apk upgrade \
    && adduser -u 5678 --disabled-password --gecos "" appuser \
    && mkdir /data && chown appuser /data

# Stage 3a: chat bot image (core + chat wheels only)
FROM runtime-base AS chat
COPY --from=builder /root/dist/initbot_core-*.whl /root/dist/initbot_chat-*.whl /tmp/
RUN --mount=type=cache,target=/root/.cache/uv,sharing=locked \
    uv venv /app \
    && VIRTUAL_ENV=/app uv pip install --compile-bytecode /tmp/*.whl \
    && rm /tmp/*.whl
USER appuser
WORKDIR /home/appuser
ENTRYPOINT ["/app/bin/initbot"]

# Stage 3b: web app image (core + web wheels only)
FROM runtime-base AS web
COPY --from=builder /root/dist/initbot_core-*.whl /root/dist/initbot_web-*.whl /tmp/
RUN --mount=type=cache,target=/root/.cache/uv,sharing=locked \
    uv venv /app \
    && VIRTUAL_ENV=/app uv pip install --compile-bytecode /tmp/*.whl \
    && rm /tmp/*.whl
USER appuser
WORKDIR /home/appuser
ENTRYPOINT ["/app/bin/initbot-web"]

# Stage 3c: remediation job image
# Behavior: runs auto_remediate.py in loop mode, so it runs until dependencies require security updates.
#   It then updates those dependency in the lock file, tests the result, and exits with an error, which causes the compose stack to exit.
#   When the compose stack exits, systemd restarts it via run.sh, which rebuilds the containers with updated dependencies and restarts the stack.
# Goals:
# - overall minimal image
# - principle of least privilege
# - minimal file set for remediation job (note bind mounts in compose.yml)
# - minimum required file permissions
FROM runtime-base AS remediator

# Make auto_remediate.py executable with a pinned runtime environment.
COPY tools/auto_remediate.py /home/appuser/tools/auto_remediate.py
# Set location of virtual environment to run script from; only required during build time, so ARG instead ENV is sufficient.
ARG VIRTUAL_ENV=/home/appuser/.venv
# Create virtual environment with script dependencies.
# Intentionally created as root user, so that it is read-only to the non-root user that runs the script.
# The "--active" option is required to make "uv sync" install the dependencies into $VIRTUAL_ENV instead of some default location.
# The "--compile-bytecode" option ensures better execution performance, given that the bytecode files can't be persisted by the non-root user running the script.
# The "uv sync --script" approach relies on auto_remediate.py to specify its own dependencies in a PEP 722 header.
# This approach is currently chosen over making auto_remediate.py a package or project as it is easier to maintain.
RUN uv sync --script /home/appuser/tools/auto_remediate.py --active --compile-bytecode

# Copy project files that auto_remediate.py operates on.
# Do not copy uv.lock because auto_remediate.py needs to operate on the up-to-date host copy, not something we bake in at build.
# Copy them as the root user, so that they are all read-only to auto_remediate.py.
COPY pyproject.toml /home/appuser/pyproject.toml
COPY packages/initbot-core/pyproject.toml /home/appuser/packages/initbot-core/pyproject.toml
COPY packages/initbot-core/src /home/appuser/packages/initbot-core/src
COPY packages/initbot-chat/pyproject.toml /home/appuser/packages/initbot-chat/pyproject.toml
COPY packages/initbot-chat/src /home/appuser/packages/initbot-chat/src
COPY packages/initbot-web/pyproject.toml /home/appuser/packages/initbot-web/pyproject.toml
COPY packages/initbot-web/src /home/appuser/packages/initbot-web/src

# auto_remediate.py expects to be run from the directory that contains the project files from above.
WORKDIR /home/appuser
# Run auto_remediate.py as non-root user to curtail its privileges.
USER appuser
# Ensure that auto_remediate.py is run from the pinned-down virtual environment via the environment's python executable.
# Invoking it directly or via uv does not guarantee this and would lead to ad-hoc dependency resolution.
ENTRYPOINT ["/home/appuser/.venv/bin/python", "/home/appuser/tools/auto_remediate.py"]
