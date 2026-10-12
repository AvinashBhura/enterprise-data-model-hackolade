# D9 — Hackolade licences and version

Status: Accepted
Date: 2026-10-12
Approved by: Avinash Bhura, in the [transition strategy document](https://claude.ai/code/artifact/5f38deb5-5ee0-414e-9516-58e23c95726c)

## Context

In-tool Git needs the Workgroup edition. The CLI in CI needs its own licence seat; Hackolade's GitHub Actions example uses a concurrent licence. Supertype groups need Studio 8.13 or later.

## Decision

Workgroup edition for modellers; a concurrent licence for CI; Studio pinned at 8.13 or later, the exact version set in `config/edm-rules.yaml` and `ci/Dockerfile`.

## Consequences

Without the CI licence, Python gates still run in CI and Hackolade steps run locally through `make` targets.
