# Implementation Plan: Bottom-Up Additive Containerization for `initbot`

This document outlines the architectural strategy and step-by-step engineering plan to transition the `initbot` project from traditional multi-stage Dockerfile image stripping to a **bottom-up, additive Nix-based container build pipeline**.

By leveraging **`uv`** as the deterministic dependency resolution source of truth, **`uv2nix`** for functional package translation, and **`nix2container`** for raw OCI rootfs assembly, this pipeline eliminates runtime package managers (`apk`, `apt`, `pip`), shells (`sh`, `bash`), and unreferenced dynamic libraries—achieving an absolute minimum attack surface and a zero-bloat runtime closure.

---

## 1. Objectives & Design Principles

* **Additive Construction (`FROM scratch` Equivalent):** Build container image layers starting from an empty root filesystem, adding *only* the specific interpreter binaries, compiled C-extensions, and shared libraries required by each service.
* **Preserve `uv` Workflow:** Maintain `pyproject.toml` and `uv.lock` as the single source of truth for Python dependency management without disrupting local development workflows.
* **Hermetic Reproducibility:** Guarantee bit-for-bit identical container closures across developer laptops and CI/CD runners using Nix content-addressed derivations.
* **Granular Multi-Service Isolation:** Separate closures precisely for distinct runtime components (e.g., chatbot, web application, and remediator services) so that a dependency in one does not bloat another.

---

## 2. Toolchain & Architecture Mapping

| Component | Role in the New Pipeline |
| --- | --- |
| **`uv` / `uv.lock**` | Local dependency resolution, package addition, and lockfile generation (`uv lock`). |
| **`uv2nix` (`pyproject-nix`)** | Translates the existing `uv.lock` file directly into pure Nix expressions (`derivations`) without conversion loss. |
| **`nix2container`** | Assembles the resolved Nix derivations and Python interpreter closures directly into an OCI image layout starting from an empty rootfs. |
| **Docker Compose** | Orchestrates the locally loaded container images identically to the previous setup. |

---

## 3. Phased Implementation Plan

### Phase 1: Establish the Nix & `uv2nix` Foundation

The goal of this phase is to establish a functional Nix flake at the repository root that bridges your existing `uv.lock` file into the Nix ecosystem.

1. **Create `flake.nix` in the Repository Root:**
Define inputs for Nixpkgs, `pyproject-nix`, and `uv2nix`.
```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    pyproject-nix.url = "github:pyproject-nix/pyproject.nix";
    uv2nix.url = "github:pyproject-nix/uv2nix";
    pyproject-build-systems.url = "github:pyproject-nix/pyproject-build-systems-pkgs";
  };

  outputs = { nixpkgs, pyproject-nix, uv2nix, pyproject-build-systems, ... } @ inputs:
    let
      supportedSystems = [ "x86_64-linux" "aarch64-linux" ];
      eachSystem = f: nixpkgs.lib.genAttrs supportedSystems (system: f {
        pkgs = import nixpkgs { inherit system; };
      });
    in
    eachSystem ({ pkgs }: {
      # Package definitions and container targets will go here
    });
}

```


2. **Ingest `uv.lock` into Nix:**
Map the workspace workspace members and dependencies using `uv2nix.lib.workspace.loadWorkspace`. This ensures Nix understands your project structure directly from your current python configuration.
3. **Verify Pure Resolution:**
Run `nix flake check` to confirm that all dependencies parse cleanly into immutable Nix dependency closures.

---

### Phase 2: Construct Minimal Runtime Closures

Instead of bundling a general-purpose Python installation, Nix constructs a minimal virtual environment containing only the required packages and transitive C-libraries.

1. **Define Service-Specific Python Environments:**
Using `pythonSet.mkVirtualEnv`, construct isolated environments for each service (chatbot, web, remediator) based on their specific profile requirements in `initbot`.
2. **Prune Unused Standard Library Components:**
Configure Nix build phases to strip out extraneous Python standard library modules that your application code never imports (e.g., GUI bindings, testing utilities, and unused localization tables).
3. **Assemble OCI Layers via `nix2container`:**
Use `nix2container` to bundle the generated environment into structured OCI layers:
* **Layer 0:** Minimal shared C-runtime libraries (`glibc` or `musl` subsets).
* **Layer 1:** Minimal Python interpreter and standard library subset.
* **Layer 2:** Compiled site-packages and application source code.



---

### Phase 3: Integrate with Docker Compose & Local Development

To ensure seamless integration with your existing local workflow, the build outputs are packed as OCI tarballs and loaded directly into the local Docker daemon.

1. **Build Container Tarballs via Nix:**
Define package outputs in your `flake.nix` for each service:
```bash
nix build .#packages.x86_64-linux.chatbot-container

```


2. **Load into Local Docker Daemon:**
Push the generated OCI archive straight into Docker for local execution:
```bash
docker load < result

```


3. **Verify Docker Compose Compatibility:**
Since `nix2container` outputs standard OCI image layouts, your existing `compose.yml` file requires zero modifications to run the resulting images.

---

### Phase 4: CI/CD Pipeline & Caching (GitHub Actions)

To maintain rapid build times in GitHub Actions, integrate Nix caching alongside Docker's GHA cache backend.

1. **Install Nix in CI:**
Add the official Determinate Systems Nix Installer action to your workflow.
2. **Enable Flake Caching:**
Cache the local Nix store (`~/.cache/nix` or GitHub Actions cache integration) to ensure dependency fetching and closure evaluation happen instantaneously across workflow runs.
3. **Automate Multi-Arch Builds:**
Leverage Nix's cross-compilation capabilities to natively build both `x86_64-linux` and `aarch64-linux` minimal container images from a single commit.

---

### Phase 5: Verification & Security Auditing

1. **Filesystem Completeness Check:**
Inspect the final image contents to ensure zero binaries like `sh`, `bash`, `pip`, or package manager registries exist:
```bash
docker run --rm --entrypoint ls chatbot-image:latest /

```


2. **SBOM & Vulnerability Tracking:**
Generate an SBOM directly from the locked Nix closure to maintain complete supply-chain visibility and verify that CVE exposure is minimized to the absolute theoretical floor.
