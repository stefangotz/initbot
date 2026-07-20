# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# Stage 1: build all three wheels
FROM ghcr.io/astral-sh/uv:python3.14-alpine@sha256:abd62675300fcbe6aa0abe17b3195294b3205eced27274458c20f6fb99ff5225 AS builder
COPY . /root/
WORKDIR /root
RUN tools/vendor-web-assets.sh
RUN --mount=type=cache,target=/root/.cache/uv \
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
FROM ghcr.io/astral-sh/uv:python3.14-alpine@sha256:abd62675300fcbe6aa0abe17b3195294b3205eced27274458c20f6fb99ff5225 AS runtime-base
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
COPY uv.lock /home/appuser/uv.lock
COPY pyproject.toml /home/appuser/pyproject.toml
COPY packages/initbot-core/pyproject.toml /home/appuser/packages/initbot-core/pyproject.toml
COPY packages/initbot-core/src /home/appuser/packages/initbot-core/src
COPY packages/initbot-chat/pyproject.toml /home/appuser/packages/initbot-chat/pyproject.toml
COPY packages/initbot-chat/src /home/appuser/packages/initbot-chat/src
COPY packages/initbot-web/pyproject.toml /home/appuser/packages/initbot-web/pyproject.toml
COPY packages/initbot-web/src /home/appuser/packages/initbot-web/src
COPY tools/auto_remediate.py /home/appuser/tools/auto_remediate.py
WORKDIR /home/appuser
USER appuser
RUN --mount=type=cache,target=/home/appuser/.cache/uv,sharing=locked \
    mkdir -p /home/appuser/.cache/uv \
    && uv venv /home/appuser/.venv \
    && VIRTUAL_ENV=/home/appuser/.venv uv sync \
    && VIRTUAL_ENV=/home/appuser/.venv uv run python3 -m compileall -j 4 packages
ENTRYPOINT ["/home/appuser/.venv/bin/python", "/home/appuser/tools/auto_remediate.py"]
