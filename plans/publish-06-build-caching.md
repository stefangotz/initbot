<!-- SPDX-FileCopyrightText: Stefan Haun <mail@tuxathome.de> -->
<!-- SPDX-License-Identifier: MIT -->

# Plan: Optimize Build Caching and Minimize Public Infrastructure Impact

## Priority

Sixth step in the container image publishing sequence. Can be implemented alongside
`publish-01` or as a follow-on once the basic publishing pipeline is in place.

## Context

Every CI run currently downloads tools, packages, and base images from public
infrastructure — PyPI, Docker Hub, GitHub Releases. This is wasteful (slow rebuilds,
redundant downloads) and puts unnecessary load on public services. With images being
published and pulled regularly, the impact compounds. BuildKit's caching model and the
GitHub Actions cache offer straightforward mitigations.

## Areas to Address

### 1. BuildKit layer caching in GitHub Actions

Without explicit cache configuration, every CI run starts from scratch. BuildKit supports
exporting and importing layer caches via the GitHub Actions cache backend:

```yaml
- uses: docker/build-push-action
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

`mode=max` caches all intermediate layers (including the builder stage), not just the final
image. This means the `uv build --wheel` step in the builder stage is skipped on cache hits.

Alternatively, `type=registry` stores the cache as a manifest in GHCR itself, which
persists across cache evictions and is accessible from any runner without relying on the
GitHub Actions cache size limits.

### 2. uv package cache in CI

The test and docker jobs both invoke `uv sync` or `uv build`, which downloads packages from
PyPI. The `astral-sh/setup-uv` action supports caching the uv package cache between runs:

```yaml
- uses: astral-sh/setup-uv
  with:
    enable-cache: true
    cache-dependency-glob: "uv.lock"
```

This caches the downloaded wheel files keyed on `uv.lock`, so PyPI is only hit when
dependencies actually change.

### 3. Trivy database caching

Trivy downloads its vulnerability database on every run. Cache it explicitly:

```yaml
- uses: actions/cache
  with:
    path: ~/.cache/trivy
    key: trivy-db-${{ github.run_id }}
    restore-keys: trivy-db-
```

Or use `aquasecurity/trivy-action` with `skip-db-update: true` after an initial download.

### 4. Audit base image and tool sources for Docker Hub pulls

Several CI steps may implicitly pull images from Docker Hub (rate-limited at 200
unauthenticated pulls per 6 hours):

- `aquasecurity/trivy-action` — check whether it pulls from Docker Hub or GHCR; prefer
  the GHCR mirror (`ghcr.io/aquasecurity/trivy`) if available, or install Trivy as a binary
  (like hadolint) to avoid any image pull.
- Any other `uses:` steps that internally `docker pull` — audit with `docker events` or
  review action source.

The base image (`ghcr.io/astral-sh/uv`) is already on GHCR — no change needed there.

### 5. Dockerfile layer ordering

Verify that Dockerfile layers are ordered from least to most frequently changing to
maximise cache reuse:

1. Base image (changes rarely — pinned to digest after `publish-03`)
2. System-level setup (user creation, directory creation)
3. Wheel installation (changes when dependencies change)
4. Application code / entrypoint (changes most often)

The current Dockerfile already follows this pattern, but confirm after any future changes.

## Expected Outcome

- CI docker build times reduce significantly on cache hits (builder stage and dependency
  downloads skipped).
- PyPI is only contacted when `uv.lock` changes, not on every CI run.
- Trivy database is cached between runs.
- No implicit Docker Hub pulls from CI jobs, eliminating rate limit risk.
- Lower aggregate load on PyPI, Docker Hub, and other public infrastructure.

## Notes

- `type=gha` cache has a 10 GB limit per repository; `type=registry` on GHCR avoids this
  constraint but requires pushing cache manifests (counts against GHCR storage, which is
  free for public repos).
- BuildKit cache is most effective when the two image targets (`chat` and `web`) share the
  builder and runtime-base stages — already the case in the current Dockerfile.
- Measure build times before and after to confirm the benefit; cache misses can occasionally
  be slower than cold builds if the cache restore itself is large.
