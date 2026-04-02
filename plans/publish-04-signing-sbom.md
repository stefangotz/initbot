<!-- SPDX-FileCopyrightText: Stefan Haun <mail@tuxathome.de> -->
<!-- SPDX-License-Identifier: MIT -->

# Plan: Image Signing and SBOM Attestation

## Priority

Fourth step in the container image publishing sequence. Depends on `publish-01` (images
must be in GHCR). Intended for a public project where supply chain transparency is expected.

## Context

With images published publicly, users and downstream tooling may want to verify:
- That a given image was actually built from this repository's CI (not tampered with)
- What software components are in the image (SBOM)

Cosign keyless signing via Sigstore uses GitHub Actions OIDC to sign images without any
long-lived private key. The signing identity is the GitHub Actions workflow itself, which
means verification is straightforward and auditable. The project already generates an SBOM
via `cyclonedx-bom` — attaching it as an OCI attestation makes it travel with the image.

SLSA Build L1 provenance is already generated automatically by `docker/build-push-action`
v4+ (implemented in `publish-01`).

## Proposed Approach

Add the following to the `docker` job in `.github/workflows/pipeline.yml`, after the push
step:

1. **Install cosign**:
   ```yaml
   - uses: sigstore/cosign-installer@<sha>  # vX.Y.Z
   ```

2. **Sign both images** using the image digest from the build step output:
   ```sh
   cosign sign --yes \
     ghcr.io/stefangotz/initbot/chat@${{ steps.build-chat.outputs.digest }}
   cosign sign --yes \
     ghcr.io/stefangotz/initbot/web@${{ steps.build-web.outputs.digest }}
   ```

3. **Attach the existing SBOM as a cosign attestation**:
   ```sh
   cosign attest --yes \
     --predicate bom.json \
     --type cyclonedx \
     ghcr.io/stefangotz/initbot/chat@${{ steps.build-chat.outputs.digest }}
   ```
   The SBOM job already uploads `bom.json` as an artifact; the docker job should download
   it (or the SBOM generation should be moved into the docker job).

## Verification (for users)

```sh
cosign verify \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  --certificate-identity-regexp https://github.com/stefangotz/initbot/.* \
  ghcr.io/stefangotz/initbot/chat:latest

cosign download attestation ghcr.io/stefangotz/initbot/chat:latest \
  | jq -r '.payload' | base64 -d | jq .
```

## Expected Outcome

- Every published image is signed with a verifiable identity (the GitHub Actions workflow).
- The SBOM is attached to each image in the registry and retrievable without a separate
  download.
- Users and compliance tooling can verify image provenance without trusting the tag.

## Notes

- `id-token: write` permission (already added in `publish-01`) is required for keyless
  signing.
- Signing attaches OCI artifacts to the registry entry; it does not change the image digest
  or require any changes to the Dockerfile or compose configuration.
- If the SBOM and docker jobs remain separate, a shared artifact (uploaded by the sbom job,
  downloaded by the docker job) is the clean solution; alternatively, merge the SBOM
  generation into the docker job.
