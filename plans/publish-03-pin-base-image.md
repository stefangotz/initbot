<!-- SPDX-FileCopyrightText: Stefan Haun <mail@tuxathome.de> -->
<!-- SPDX-License-Identifier: MIT -->

# Plan: Pin Base Image to Digest and Enable Dependabot

## Priority

Third step in the container image publishing sequence. Can be done independently of
`publish-02`, but should precede `publish-04` (signing) to establish a reproducible build
baseline.

## Context

The Dockerfile currently references the base image by tag:
`ghcr.io/astral-sh/uv:python3.14-alpine`. Tags are mutable — the same tag can be
re-pushed with different content, silently changing what the build produces. Pinning to a
digest (`@sha256:…`) makes builds reproducible and ensures CI can detect when the base
image changes (rather than silently accepting a new one).

Dependabot supports Docker base image digest updates and will open automated PRs when a
new digest is published for the pinned tag, keeping the pin current without manual effort.

## Proposed Approach

1. Resolve the current digest for `ghcr.io/astral-sh/uv:python3.14-alpine`:
   ```sh
   docker buildx imagetools inspect ghcr.io/astral-sh/uv:python3.14-alpine \
     --format '{{json .Manifest}}' | jq -r '.digest'
   ```

2. Update the `FROM` lines in `Dockerfile` to pin the digest:
   ```dockerfile
   FROM ghcr.io/astral-sh/uv:python3.14-alpine@sha256:<digest> AS builder
   # …
   FROM ghcr.io/astral-sh/uv:python3.14-alpine@sha256:<digest> AS runtime-base
   ```
   Keep the tag in the reference (before `@sha256`) so Dependabot can match and update it.

3. Add or extend `.github/dependabot.yml` to enable Docker ecosystem updates:
   ```yaml
   version: 2
   updates:
     - package-ecosystem: docker
       directory: /
       schedule:
         interval: weekly
   ```

## Expected Outcome

- Builds are reproducible: the same source tree always produces the same image layers.
- Changes to the base image are explicit (a Dependabot PR) rather than silent.
- Dependabot handles routine digest bumps automatically, keeping the base image current.

## Notes

- The digest is architecture-specific for single-platform builds. For `linux/amd64` only
  (current scope), a single digest is sufficient.
- `hadolint` may warn if the tag is omitted from the `FROM` line; keeping both tag and
  digest (`tag@sha256:…`) satisfies hadolint and Dependabot alike.
