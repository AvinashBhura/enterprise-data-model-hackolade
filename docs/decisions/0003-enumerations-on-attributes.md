# D3 — Enumerations live on attributes; the EDM stores no reference data

Status: Accepted
Date: 2026-10-12
Approved by: Avinash Bhura, in the [transition strategy document](https://claude.ai/code/artifact/5f38deb5-5ee0-414e-9516-58e23c95726c)

## Context

The LinkML EDM had 68 enum schemas, including partial ISO code lists. Hackolade supports an `enum` list on an attribute or definition, without per-value descriptions.

## Decision

Closed lists (lifecycle states, types) are `enum` lists on the attribute of the owning entity; value meanings go in the `valueDefinitions` custom property. ISO code lists (currency, country, language, unit of measure) become format rules with the standard named; no values are stored. Taxonomies are data, held by the Common taxonomy model (D11). The EDM is a schema store only.

## Consequences

Generated schemas still enforce closed lists (CHECK constraints, JSON Schema `enum`). Applications validate ISO codes against one shared source, never their own hard-coded lists. `check_enums` flags copies of the same enum that drift apart.
