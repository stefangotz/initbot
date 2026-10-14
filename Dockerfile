# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# Pin uv and Python.
# The hashes are platform-independent manifest hashes instead of image hashes. Obtain manifest hashes via `docker buildx imagetools inspect IMG_NAME:LABEL`.
# Use the exact same version as in uv-version.sh; it needs to support the Python version below.
FROM ghcr.io/astral-sh/uv:0.13.6-alpine@sha256:95f501aef734a5aaf167ff0640e02f215dcc7043ff48685de70328e5c55a57b0 AS uv
# Use the exact same Python version as in .python-version
FROM python:3.15.2-alpine3.24@sha256:1656b7eaf309cadf99069ea9de335c7f67a8355789cfc6f1835a05818996f081 AS python

FROM python AS python-uv
# The upstream uv-python images can sometimes lag uv and Python releases quite significantly.
# Therefore, we combine uv and Python by copying uv into the Python image, which is currently the recommended and documented approach to use containerised uv.
COPY --from=uv /usr/local/bin/uv* /usr/local/bin/

# Build all three wheels and prep installation into venv in /app
FROM python-uv AS pkg-builder
RUN --mount=type=cache,target=/var/cache/apk \
    # build-base provides gcc and g++.
    # Those are required to install Python packages, such as pydantic-core.
    # Why do they build from source instead of using wheels?
    # At least in the case of pydantic-core, pypi seems to provide wheels only for the most recent release and no other version.
    # Since we pin all our Python dependencies, including pydantic-core, they can fall behind their most recent releases at any time, so they usually are "old".
    # Thus, when installing pydantic-core, for example, there are no wheels to draw on and thus installing it requires build tools.
    # Unfortunately, this also more or less guarantees that builds are not reproducible long term.
    apk add build-base=0.5-r4 \
    && uv venv /app
COPY . /root/
WORKDIR /root
RUN tools/vendor-web-assets.sh
RUN --mount=type=cache,target=/root/.cache/uv,sharing=locked \
    uv build --package initbot-core --wheel \
    && uv build --package initbot-chat --wheel \
    && uv build --package initbot-web --wheel \
    && uv export --frozen --no-dev --no-emit-local --format requirements.txt > /root/constraints.txt

# install initbot-chat into /app
FROM pkg-builder AS chat-installer
RUN --mount=type=cache,target=/root/.cache/uv,sharing=locked \
    VIRTUAL_ENV=/app uv pip install --compile-bytecode --constraints /root/constraints.txt /root/dist/initbot_core-*.whl /root/dist/initbot_chat-*.whl

# install initbot-web into /app
FROM pkg-builder AS web-installer
RUN --mount=type=cache,target=/root/.cache/uv,sharing=locked \
    VIRTUAL_ENV=/app uv pip install --compile-bytecode --constraints /root/constraints.txt /root/dist/initbot_core-*.whl /root/dist/initbot_web-*.whl

# common properties of chat and web execution images
FROM python AS runtime-base
ARG USER_NAME=appuser
ARG USER_ID=5678
ARG USER_HOME=/home/$USER_NAME
RUN adduser -u $USER_ID --disabled-password --gecos "" $USER_NAME

# chat bot image (copying /app venv from chat-installer layer)
FROM runtime-base AS chat
COPY --from=chat-installer /app /app
# hadolint ignore=DL3066
USER $USER_NAME
WORKDIR $USER_HOME
ENTRYPOINT ["/app/bin/initbot"]

# web app image (copying /app venv from web-installer layer)
FROM runtime-base AS web
COPY --from=web-installer /app /app
# hadolint ignore=DL3066
USER $USER_NAME
WORKDIR $USER_HOME
ENTRYPOINT ["/app/bin/initbot-web"]

# remediation job image
# Behavior: runs auto_remediate.py in loop mode, so it runs until dependencies require security updates.
#   It then updates those dependency in the lock file, tests the result, and exits with an error, which causes the compose stack to exit.
#   When the compose stack exits, systemd restarts it via run.sh, which rebuilds the containers with updated dependencies and restarts the stack.
# Goals:
# - overall minimal image
# - principle of least privilege
# - minimal file set for remediation job (note bind mounts in compose.yml)
# - minimum required file permissions
FROM runtime-base AS remediator
COPY --from=uv /usr/local/bin/uv* /usr/local/bin/
# Set location of virtual environment to run script from; only required during build time, so ARG instead ENV is sufficient.
ARG VIRTUAL_ENV=/app
# Pre-create venv (as opposed to letting 'uv sync' do it) because otherwise uv sync complains about auto_remediate.py already being in /app
RUN --mount=type=cache,target=/root/.cache/uv,sharing=locked \
    uv venv $VIRTUAL_ENV
# Make auto_remediate.py executable with a pinned runtime environment.
COPY tools/auto_remediate.py $VIRTUAL_ENV/auto_remediate.py
# Create virtual environment with script dependencies.
# Intentionally created as root user, so that it is read-only to the non-root user that runs the script.
# The "--active" option is required to make "uv sync" install the dependencies into $VIRTUAL_ENV instead of some default location.
# The "--compile-bytecode" option ensures better execution performance, given that the bytecode files can't be persisted by the non-root user running the script.
# The "uv sync --script" approach relies on auto_remediate.py to specify its own dependencies in a PEP 722 header.
# This approach is currently chosen over making auto_remediate.py a package or project as it is easier to maintain.
RUN uv sync --script $VIRTUAL_ENV/auto_remediate.py --active --compile-bytecode

# Copy project files that auto_remediate.py operates on.
# Do not copy uv.lock because auto_remediate.py needs to operate on the up-to-date host copy, not something we bake in at build.
# Copy them as the root user, so that they are all read-only to auto_remediate.py.
COPY pyproject.toml $USER_HOME/pyproject.toml
COPY packages/initbot-core/pyproject.toml $USER_HOME/packages/initbot-core/pyproject.toml
COPY packages/initbot-core/src $USER_HOME/packages/initbot-core/src
COPY packages/initbot-chat/pyproject.toml $USER_HOME/packages/initbot-chat/pyproject.toml
COPY packages/initbot-chat/src $USER_HOME/packages/initbot-chat/src
COPY packages/initbot-web/pyproject.toml $USER_HOME/packages/initbot-web/pyproject.toml
COPY packages/initbot-web/src $USER_HOME/packages/initbot-web/src

# auto_remediate.py expects to be run from the directory that contains the project files from above.
WORKDIR $USER_HOME
# Run auto_remediate.py as non-root user to curtail its privileges.
# hadolint ignore=DL3066
USER $USER_NAME
# Ensure that auto_remediate.py is run from the pinned-down virtual environment via the environment's python executable.
# Invoking it directly or via uv does not guarantee this and would lead to ad-hoc dependency resolution.
ENTRYPOINT ["/app/bin/python", "/app/auto_remediate.py"]
