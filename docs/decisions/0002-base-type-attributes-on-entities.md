# D2 — Base-type attributes are declared on each entity

Status: Accepted
Date: 2026-10-12
Approved by: Avinash Bhura, in the [transition strategy document](https://claude.ai/code/artifact/5f38deb5-5ee0-414e-9516-58e23c95726c)

## Context

In LinkML, base types (Identifiable, Lifecycleable, Temporal, Classifiable, Addressable, RoleHolder) were mixins. Hackolade has no mixins.

## Decision

Each entity declares its base-type attributes directly and lists the base types it follows in the `edmComposes` custom property. Each base type's contract (attribute names, types, required flags, descriptions) is written once in `config/edm-rules.yaml`, and `check_base_types` verifies every entity against it. Composite value types (AmountType, QuantityType, DocumentType, StateTransition, NaturalIdentifier) stay shared definitions in Common, reused by external reference.

## Consequences

Simple to model in Hackolade and simple to read. The same attributes repeat across entities, so drift is possible; the contract check catches it.
