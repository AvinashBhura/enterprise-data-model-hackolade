# D4 — Hackolade generates all schemas and documents

Status: Accepted
Date: 2026-10-12
Approved by: Avinash Bhura, in the [transition strategy document](https://claude.ai/code/artifact/5f38deb5-5ee0-414e-9516-58e23c95726c)

## Context

The LinkML repository had Python generators for JSON Schema, Pydantic classes and SQL DDL.

## Decision

Hackolade generates every artifact (DDL, JSON Schema, Avro, OpenAPI, documentation) through `forwEng`, `genDoc`, `polyglotDerive` and `compMod`. No Python generators. Python only checks. Generated files are not committed here; CI builds and publishes them on each tag. Application repositories commit their own DDL next to their code.

## Consequences

The Pydantic generator is retired. Teams that need classes generate them from the published JSON Schema with standard tools.
