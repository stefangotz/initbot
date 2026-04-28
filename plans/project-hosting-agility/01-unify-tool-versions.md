<!-- SPDX-FileCopyrightText: Stefan Haun <mail@tuxathome.de> -->
<!-- SPDX-License-Identifier: MIT -->

# Plan: Unify Tool Versions Under uv

## Priority

First step in the CI/CD independence sequence. Lowest effort, highest immediate benefit.

## Problem

Several dev tools are version-pinned in two places: as uv dev dependencies in `pyproject.toml`
and as independent installs in `.pre-commit-config.yaml`. This creates a real version drift risk.
The most acute case is ruff: pre-commit hard-pins `v0.15.6` while pyproject.toml has `>=0.9.0`.
If uv resolves ruff to a newer minor version, pre-commit and CI lint with different rules.

Other duplicated tools: zizmor, reuse, detect-secrets. Binary tools shellcheck and hadolint have
no uv entry at all — pre-commit manages them in isolated environments, CI downloads the binaries
separately.

## Proposed Approach

1. Add `shellcheck-py` and `hadolint-py` to `[tool.uv.dev-dependencies]` in root `pyproject.toml`.
2. Convert all non-local pre-commit hooks (ruff, detect-secrets, shellcheck, hadolint, reuse,
   zizmor) to `local` hooks that call `uv run <tool>`.
3. Remove the version pins from `.pre-commit-config.yaml` for those tools — uv's lock file
   becomes the single source of truth.

## Expected Outcome

- Version drift between pre-commit and CI becomes impossible.
- `uv sync` is the only setup step needed to get a consistent dev environment.
- Simpler `.pre-commit-config.yaml` with fewer external sources to update.
- `uv.lock` captures exact versions of all dev tools, improving reproducibility.

## Notes

- The `pre-commit-hooks` source (check-yaml, end-of-file-fixer, etc.) provides only generic
  file-level checks with no version-sensitive output; it can reasonably stay external.
- Trivy (container vulnerability scanning) and cyclonedx-bom (SBOM) are CI-only and have no
  pre-commit equivalent — leave them as-is.
- After this step, pre-commit becomes entirely local/uv-based, matching CI exactly.
