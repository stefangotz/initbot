# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# Stage 1: build all three wheels
FROM ghcr.io/astral-sh/uv:python3.14-alpine@sha256:4ee7a28b72cca1e67b77e86170ab941db4748cea9e8b77eeac3fd0738a1ee57d AS builder
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
FROM ghcr.io/astral-sh/uv:python3.14-alpine@sha256:4ee7a28b72cca1e67b77e86170ab941db4748cea9e8b77eeac3fd0738a1ee57d AS runtime-base
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
