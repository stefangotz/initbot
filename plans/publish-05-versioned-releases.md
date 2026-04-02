<!-- SPDX-FileCopyrightText: Stefan Haun <mail@tuxathome.de> -->
<!-- SPDX-License-Identifier: MIT -->

# Plan: Versioned Image Releases

## Priority

Fifth step in the container image publishing sequence, and the most deferred. Should only
be pursued once there is a concrete need for stable, pinnable image references — either
because external users ask for them or because the deployment model warrants it.

## Context

The project currently publishes only a `latest` tag. This is sufficient for personal
deployment and early public availability, but has limitations:

- Users cannot pin to a known-good version
- Rolling back requires knowing the exact SHA of a previous image
- `latest` is mutable, so `docker compose pull` may silently introduce breaking changes

Proper versioned releases tie image tags to git tags and GitHub Releases, making the
`latest` → versioned upgrade path explicit and controlled.

The pipeline already fires on GitHub `release` events (a prepared hook).

## Proposed Approach

### 1. Establish a versioning workflow

- Adopt semantic versioning (`MAJOR.MINOR.PATCH`)
- Version is currently hardcoded at `0.1.0` in all three `pyproject.toml` files; bumping
  requires updating all three
- Consider a tool to automate version bumps across packages (e.g., `bump-my-version`,
  `release-please`, or a simple script)
- Create git tags (`v1.2.3`) and GitHub Releases as the release trigger

### 2. Add semver tag variants via `docker/metadata-action`

`docker/metadata-action` handles the tag hierarchy automatically when triggered by a git
tag event:

```yaml
tags:
  - type: semver
    pattern: "{{version}}"        # v1.2.3
  - type: semver
    pattern: "{{major}}.{{minor}}" # v1.2
  - type: semver
    pattern: "{{major}}"           # v1
  - type: raw
    value: latest
    enable: ${{ github.ref == 'refs/heads/main' }}
```

No other CI changes are needed beyond this metadata-action configuration update.

### 3. Update `compose.yml` for optional version pinning

When versioned images exist, operators who want stability can pin:

```yaml
services:
  chat:
    image: ghcr.io/stefangotz/initbot/chat:v1.2.3
```

The `latest`-based default continues to work for users who prefer automatic updates.

### 4. Add a changelog

A `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/) convention
provides release notes alongside the GitHub Release. Can be maintained manually or
automated with `git-cliff` (Conventional Commits) or `release-please`.

## Expected Outcome

- Each GitHub Release produces images tagged `vMAJOR.MINOR.PATCH`, `vMAJOR.MINOR`,
  `vMAJOR`, and `latest`.
- Users can pin to any level of specificity.
- Release notes are published alongside each image.
- Rolling back is a one-line change to the image tag.

## Notes

- The version bump process (three `pyproject.toml` files) is the main friction point.
  Tooling or a release script should handle this to keep it low-overhead.
- Decide whether releases are manual (human creates the GitHub Release) or automated
  (e.g., `release-please` opens a release PR on every conventional commit).
