<!-- SPDX-FileCopyrightText: Stefan Haun <mail@tuxathome.de> -->
<!-- SPDX-License-Identifier: MIT -->

# Plan: Container-Based CI

## Priority

Third step in the CI/CD independence sequence. Builds on the shared check script (plan 02).
Higher complexity; should only be pursued if portability or local reproducibility become
active needs.

## Problem

CI jobs are defined as GitHub Actions steps and depend on GitHub-specific infrastructure
(runners, Actions ecosystem, OIDC, etc.). Running CI locally requires either pushing a branch
or using imperfect emulation tools like `act`. The more CI logic lives in GitHub-specific YAML,
the harder it is to reason about locally or move to another provider.

## Proposed Approach

Build a CI container image that bundles the Python toolchain, uv, and all dev dependencies.
GitHub Actions becomes a thin wrapper: check out the repo, pull the image, run it.

Key decisions to make during implementation planning:

- **Image registry**: GHCR (free, integrated) vs Docker Hub vs build fresh each run.
- **Image update strategy**: rebuild on changes to `uv.lock` or `pyproject.toml`; tag by lock
  file hash for exact reproducibility.
- **Entrypoint**: the `tools/check.sh` script from plan 02 is the natural container entrypoint.
- **Tooling**: raw Docker + shell scripts, or a purpose-built tool like
  [Earthly](https://earthly.dev/) or [Dagger](https://dagger.io/) that provides better caching
  and local/CI parity out of the box.

Resulting CI workflow structure:

```yaml
- uses: actions/checkout
- run: docker pull ghcr.io/…/ci:$LOCK_HASH || docker build -t ci:$LOCK_HASH -f Dockerfile.ci .
- run: docker run --rm -v $PWD:/repo ci:$LOCK_HASH /repo/tools/check.sh
```

## Expected Outcome

- Any CI provider that can run containers can run the checks identically.
- Developers can reproduce CI locally with a single `docker run` command.
- GitHub Actions YAML is reduced to infrastructure boilerplate; no tool-specific logic lives there.
- Switching CI providers requires only updating the thin wrapper, not re-specifying checks.

## Risks and Downsides

- **Cold build time**: if the CI image is not cached, building it adds 3–8 minutes to CI runs.
  Requires a solid caching strategy (GHCR layer cache, BuildKit cache mounts).
- **Second Dockerfile**: a `Dockerfile.ci` (or `Dockerfile.dev`) adds another image to maintain
  alongside the application Dockerfiles.
- **Circular dependency**: the image that runs the checks is built in the same CI that runs the
  checks. Bootstrapping failures can block CI.
- **Pre-commit interaction**: git hooks run in the developer's shell, not inside a container.
  Pre-commit hooks still need local tool access (plan 01/02 handle this).

## Notes

- This step is optional and should be deferred until there is a concrete need (e.g., local CI
  reproducibility complaints, a planned migration away from GitHub, or desire to test on
  self-hosted runners).
- Plans 01 and 02 deliver the majority of the de-coupling benefit at a fraction of the complexity.
  With those in place, adding a container later is straightforward.
