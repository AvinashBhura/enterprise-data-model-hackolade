# D6 — Scope of migration

Status: Accepted
Date: 2026-10-12
Approved by: Avinash Bhura, in the [transition strategy document](https://claude.ai/code/artifact/5f38deb5-5ee0-414e-9516-58e23c95726c)

## Context

The LinkML repository holds eight non-HR domains, seven sample processes and five sample application models. The brief asks for HR, the core process model and one application model, and no extra examples.

## Decision

Migrate Foundation, Common, HR, the core process model and `04_application/_shared`. Retire the seven sample processes and five sample application models (Okta, SAP, Salesforce, ServiceNow, Workday). Freeze non-HR domains: tag `linkml-final-v0.5.0`, remove them from the tree, and list them in `docs/migration-backlog.md`.

## Consequences

Each frozen domain is migrated later under its own spec. Until then, references to frozen domains are typed keys.
