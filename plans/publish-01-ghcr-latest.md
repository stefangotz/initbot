<!-- SPDX-FileCopyrightText: Stefan Haun <mail@tuxathome.de> -->
<!-- SPDX-License-Identifier: MIT -->

# Plan: Publish `latest` Images to GHCR

## Priority

First step in the container image publishing sequence. Core change that everything else
builds on.

## Context

The project builds two Docker images in CI (`chat` and `web`) and runs Trivy scans on them,
but does not push them anywhere. The intended audience is the wider open-source public.
GHCR is the natural registry choice: it is already used for the base image
(`ghcr.io/astral-sh/uv:python3.14-alpine`), is free for public repositories, and
authenticates via `GITHUB_TOKEN` with no secrets to manage.

## Proposed Approach

Extend the existing `docker` job in `.github/workflows/pipeline.yml`:

1. Add `packages: write` and `id-token: write` permissions to the job.
2. Add `docker/login-action` to authenticate with GHCR using `GITHUB_TOKEN`.
3. Add `docker/setup-buildx-action` to enable BuildKit.
4. Add `docker/metadata-action` to generate OCI-compliant labels and the `latest` tag.
5. Replace the manual `docker build` steps with `docker/build-push-action`, which builds
   and pushes in one step.
6. Gate publishing on `github.event_name != 'pull_request'` so fork PRs cannot push images.
7. Continue running Trivy after build; push only if the scan passes.

Published image names:
- `ghcr.io/stefangotz/initbot/chat:latest`
- `ghcr.io/stefangotz/initbot/web:latest`

OCI labels generated automatically by `docker/metadata-action`:
`org.opencontainers.image.{source, revision, created, version, licenses, title, description}`

## Expected Outcome

- Both images are pushed to GHCR on every merge to main.
- The `latest` tag always reflects the most recent successful main build.
- Image metadata is complete and discoverable in the GitHub repository's Packages tab.
- No secrets to manage — authentication is entirely via `GITHUB_TOKEN`.

## Notes

- SLSA Build L1 provenance is generated automatically by `docker/build-push-action` v4+.
- Use BuildKit inline caching (`cache-from: type=gha`, `cache-to: type=gha,mode=max`) to
  keep CI build times reasonable.
- Versioned tags (semver) are not part of this step — see `publish-05-versioned-releases.md`.
