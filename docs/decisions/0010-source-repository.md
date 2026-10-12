# D10 — Source of truth for migration

Status: Accepted
Date: 2026-10-12
Approved by: Avinash Bhura, in the [transition strategy document](https://claude.ai/code/artifact/5f38deb5-5ee0-414e-9516-58e23c95726c)

## Context

The migration needs one authoritative LinkML source.

## Decision

`~/enterprise-data-model` (GitHub `AvinashBhura/enterprise-data-model`), branch `main` at commit `9ad895d`. Its model content matches v0.5.0.

## Consequences

The tag `linkml-final-v0.5.0` is set on this commit before anything is removed. The Hackolade EDM itself lives in a separate repository ([D13](0013-separate-hackolade-repository.md)).
