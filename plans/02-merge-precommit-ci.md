<!-- SPDX-FileCopyrightText: Stefan Haun <mail@tuxathome.de> -->
<!-- SPDX-License-Identifier: MIT -->

# Plan: Merge Pre-commit and CI Infrastructure

## Priority

Second step in the CI/CD independence sequence. Builds on unified tool versions (plan 01).
Moderate effort, clear structural benefit.

## Problem

The same checks are listed in two files — `.pre-commit-config.yaml` and
`.github/workflows/pipeline.yml` — with no formal link between them. Adding a new check means
updating both files. After plan 01, version drift is gone, but the structural duplication remains:
CI and pre-commit are parallel systems that happen to run the same tools.

## Proposed Approach

Extract a shared check script (`tools/check.sh` or similar) that contains all quality checks as
plain `uv run <tool>` invocations. Both pre-commit hooks and CI steps call this script (or
specific functions within it) rather than specifying tools directly.

Pre-commit retains its role as git hook plumbing and handles staged-file filtering (only linting
files you've actually changed). The check script handles the "run everything" case used by CI and
by developers who want a full local check.

Rough structure:

- `tools/check.sh` — runs lint, type check, dead-code, license, secret, and shell/Dockerfile
  audits via `uv run`
- Pre-commit `local` hooks delegate to `uv run <tool>` (consistent with plan 01)
- CI steps source or call `check.sh` instead of duplicating tool invocations

## Expected Outcome

- Adding or changing a check requires editing one place.
- Developers can run `tools/check.sh` locally to replicate CI exactly, without needing to trigger
  a full pre-commit run.
- CI workflow file becomes a thin orchestrator (setup uv, call script, report results) rather than
  a list of tool invocations.
- Groundwork for optional containerisation (plan 03): the check script is the natural container
  entrypoint.

## Notes

- Pre-commit's value (staged-file filtering, parallelism, hook caching) is preserved. It still
  runs the tools; it just no longer specifies which version or how to invoke them independently
  of uv.
- Tests (pytest) and coverage are naturally part of the script too, though slower checks may
  warrant a separate "fast" vs "full" split.
- This step does not yet involve containers — it just moves the check definitions to a script.
