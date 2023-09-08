# A container for building the initbot dist with poetry
FROM python:slim

# Install poetry
RUN apt update && apt install -y wget
RUN wget -qO - https://install.python-poetry.org | python3 -
ENV PATH=$PATH:/root/.local/bin

# Bring in the initbot Python code
COPY . /root/
WORKDIR /root
# Build the initbot dist
RUN poetry build



# A container for running initbot
FROM python:slim
# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1
# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && mkdir -p /app
# Copy over the initbot dist from the build layer
COPY --from=0 /root/dist/*.tar.gz /app/
RUN chown -R appuser /app
USER appuser
WORKDIR /app
ENV PATH=$PATH:/home/appuser/.local/bin
RUN pip3 install --user /app/initbot-0.1.0.tar.gz

CMD python3 -m initbot
