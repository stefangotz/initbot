# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# Stage 1: build all three wheels
FROM ghcr.io/astral-sh/uv:python3.14-alpine AS builder
COPY . /root/
WORKDIR /root
RUN uv build --package initbot-core --wheel \
    && uv build --package initbot-chat --wheel \
    && uv build --package initbot-web --wheel

# Stage 2: shared OS configuration (no packages)
FROM ghcr.io/astral-sh/uv:python3.14-alpine AS runtime-base
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN apk upgrade --no-cache \
    && adduser -u 5678 --disabled-password --gecos "" appuser \
    && mkdir /data && chown appuser /data

# Stage 3a: chat bot image (core + chat wheels only)
FROM runtime-base AS chat
COPY --from=builder /root/dist/initbot_core-*.whl /root/dist/initbot_chat-*.whl /tmp/
RUN uv venv /app \
    && export VIRTUAL_ENV=/app \
    && uv pip install --no-cache --compile-bytecode /tmp/*.whl \
    && rm /tmp/*.whl
USER appuser
WORKDIR /home/appuser
ENTRYPOINT ["/app/bin/initbot"]

# Stage 3b: web app image (core + web wheels only)
FROM runtime-base AS web
COPY --from=builder /root/dist/initbot_core-*.whl /root/dist/initbot_web-*.whl /tmp/
RUN uv venv /app \
    && export VIRTUAL_ENV=/app \
    && uv pip install --no-cache --compile-bytecode /tmp/*.whl \
    && rm /tmp/*.whl
USER appuser
WORKDIR /home/appuser
ENTRYPOINT ["/app/bin/initbot-web"]
