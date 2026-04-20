# Contributing to Initbot

## Prerequisites

- [uv](https://docs.astral.sh/uv/) — Python package manager
- Git
- A Discord bot token if you want to test the chat bot end-to-end

## Setting Up a Development Environment

Run the setup script (Linux or macOS):

```sh
./tools/set_up_dev.sh
```

This installs uv, creates a virtual environment in `.venv/`, installs all dependencies, and wires up pre-commit hooks. On Windows the script won't run directly, but each step translates straightforwardly to Windows equivalents.

## Running the Tests

```sh
uv run pytest
```

Tests require 80% coverage; `coverage report` enforces this automatically.

## Code Style and Quality

Pre-commit hooks run automatically on `git commit` and enforce formatting, linting, type checking, dead-code detection, secret scanning, and licence header verification. Run them manually at any time:

```sh
uv run pre-commit run --all-files
```

## Workflow

1. Fork the repository and create a feature branch from `main`.
2. Make your changes and add tests where appropriate.
3. Ensure all pre-commit hooks and CI checks pass.
4. Open a pull request against `main`.

## Reporting Issues

- **Security vulnerabilities** — use [GitHub private vulnerability reporting](https://github.com/stefangotz/initbot/security/advisories/new). See [SECURITY.md](SECURITY.md) for details.
- **Bugs and feature requests** — open a [GitHub issue](https://github.com/stefangotz/initbot/issues).

## Licence

By contributing you agree that your contributions will be licenced under [AGPL-3.0-or-later](LICENSES/AGPL-3.0-or-later.txt).
