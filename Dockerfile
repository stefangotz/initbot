# A container for building the initbot dist
FROM ghcr.io/astral-sh/uv:python3.13-alpine

# Bring in the initbot Python code
COPY . /root/
WORKDIR /root
# Build the initbot dist
RUN uv build --wheel



# A container for running initbot
FROM ghcr.io/astral-sh/uv:python3.13-alpine
# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1
# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

COPY --from=0 /root/dist/*.whl /tmp/
RUN uv venv /app && export VIRTUAL_ENV=/app && uv pip install --no-cache --compile-bytecode /tmp/initbot-*.whl && rm /tmp/initbot-*.whl

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser
USER appuser
WORKDIR /home/appuser
ENTRYPOINT ["/app/bin/initbot"]
