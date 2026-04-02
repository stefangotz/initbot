<!-- SPDX-FileCopyrightText: Stefan Haun <mail@tuxathome.de> -->
<!-- SPDX-License-Identifier: MIT -->

# Plan: Switch Deployment to Pull Pre-Built Images

## Priority

Second step in the container image publishing sequence. Depends on `publish-01` (images
must exist in GHCR before this is useful).

## Context

The current deployment builds images from source on the server via `docker compose build`
in `tools/run_compose.sh`. Now that images are published to GHCR, deployment can pull
pre-built images instead: faster, reproducible, and no build tooling required on the server.

Docker Compose natively supports both modes via the `image` + `build` dual-key pattern.
Having both keys in a service definition means:
- `docker compose pull` pulls the named image from the registry
- `docker compose build` builds locally and names the result with the `image:` value
- `docker compose up` starts whichever image is already present locally

This preserves the ability to build from source without any configuration change.

## Proposed Approach

1. Add `image:` keys to both application services in `compose.yml`:

   ```yaml
   services:
     chat:
       image: ghcr.io/stefangotz/initbot/chat:latest
       build:
         context: .
         target: chat
     web:
       image: ghcr.io/stefangotz/initbot/web:latest
       build:
         context: .
         target: web
   ```

2. Update `tools/run_compose.sh` to pull instead of build:

   ```sh
   docker compose pull
   exec docker compose up
   ```

## Expected Outcome

- Default deployment (`tools/run_compose.sh`) pulls and starts the pre-built GHCR images.
- Building from source remains available: `docker compose build && docker compose up`.
- Server no longer needs the full source tree or build tooling to deploy updates.
- Deploying a new release is: `docker compose pull && docker compose up -d`.

## Notes

- Caddy and any other non-application services in `compose.yml` are unaffected (they
  already use `image:` references).
- The `image:` tag is `latest` for now. When versioned releases are established
  (see `publish-05-versioned-releases.md`), this can be updated to pin a specific version.
