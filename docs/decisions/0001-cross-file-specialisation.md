# D1 — How a Domain entity specialises a Foundation entity

Status: Accepted
Date: 2026-10-12
Approved by: Avinash Bhura, in the [transition strategy document](https://claude.ai/code/artifact/5f38deb5-5ee0-414e-9516-58e23c95726c)

## Context

Hackolade supertype groups (v8.13+) work inside one model. A Domain entity must specialise a Foundation entity that lives in another model file. Hackolade has no cross-file inheritance.

## Decision

Each domain polyglot model derives the Foundation entities it needs from `Foundation.hck.json`, then declares its entities as subtypes of them in local supertype groups. Derived Foundation entities are not edited. Domain supertype groups use the roll-down strategy.

## Consequences

Foundation entities appear (as derived copies) in each domain model that uses them. Updates flow through `polyglotUpdate`, and the stale gate in CI catches a missed refresh. If spike T2 shows an external reference can act as a supertype, this decision is revisited to use references instead of derived copies.
