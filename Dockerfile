# Stage 1: build all three wheels
FROM ghcr.io/astral-sh/uv:python3.14-alpine AS builder
COPY . /root/
WORKDIR /root
RUN uv build --package initbot-core --wheel \
    && uv build --package initbot-chat --wheel \
    && uv build --package initbot-web --wheel

# Stage 2: install wheels into shared venv
FROM ghcr.io/astral-sh/uv:python3.14-alpine AS base
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
COPY --from=builder /root/dist/*.whl /tmp/
RUN uv venv /app \
    && export VIRTUAL_ENV=/app \
    && uv pip install --no-cache --compile-bytecode /tmp/*.whl \
    && rm /tmp/*.whl
RUN adduser -u 5678 --disabled-password --gecos "" appuser
USER appuser
WORKDIR /home/appuser

# Stage 3a: chat bot image
FROM base AS chat
ENTRYPOINT ["/app/bin/initbot"]

# Stage 3b: web app image
FROM base AS web
ENTRYPOINT ["/app/bin/initbot-web"]
