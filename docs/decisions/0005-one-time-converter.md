# D5 — Existing models move across with a one-time converter

Status: Accepted
Date: 2026-10-12
Approved by: Avinash Bhura, in the [transition strategy document](https://claude.ai/code/artifact/5f38deb5-5ee0-414e-9516-58e23c95726c)

## Context

About 130 LinkML classes need to become Hackolade models. Hackolade's model file is plain JSON but not a published contract.

## Decision

A one-time Python converter writes `.hck.json` files in Hackolade's own structure (persistence schema 8). Each file is opened and saved in Studio before commit. The converter is deleted after migration. After that, Python reads model files but never writes them.

## Consequences

Spike T4 must confirm converter output opens and derives cleanly. If it does not, migration uses Hackolade's documented Excel template import instead.
