# Data Domain Organization

> Reference: this document explains how the Domain layer is physically organized
> and the rules for placing new entities. Read alongside `principles.md`.

## Three-Level Hierarchy

The Domain layer (`src/02_domain/`) is organized in three levels:

```text
02_domain/
└── <RootDomain>/                 ← Level 1: business function (HR, Finance, Sales, ...)
    ├── _shared/                  ← definitions shared by its subdomains, with no single owner
    └── <SubDomain>/              ← Level 2: capability cluster (TalentAcquisition, CoreHR, ...)
        └── <SubDomain>.hck.json  ← one polyglot model; its entities are the Level 3 data domains
```

### Level 1: Root Domain

A **root domain** corresponds to a major business function — typically the
top-level capability area in the enterprise capability map.

Root domains: `HR` (six subdomain models, [src/02_domain/HR](../../src/02_domain/HR/README.md)). `Finance`, `Sales`, `Procurement`, `Legal`,
`Security`, `IT`, `Facilities` and `Governance` are frozen until migrated
(see [migration-backlog.md](../migration-backlog.md)).

A root domain is stewarded by a senior business owner (CHRO for HR, CFO for
Finance, etc.). Adding a new root domain is a significant architectural
decision and should be reviewed by the data architecture committee.

### Level 2: Sub-Domain

A **sub-domain** corresponds to a capability cluster within a business
function — typically aligning with a department, function, or service line.

Examples:
- `HR/TalentAcquisition` — recruiting and hiring
- `HR/CoreHR` — employee lifecycle management
- `Finance/GeneralLedger` — core accounting
- `Sales/CustomerManagement` — customer relationship management

A sub-domain is stewarded by a functional owner reporting to the root-domain
owner. Sub-domain boundaries are stable but may shift on reorganization.

### Level 3: Data Domain

A **data domain** is a logical grouping of related entities within a sub-domain.
In Hackolade, a sub-domain's data domains are entities in its one polyglot
model, classified Core, Supporting or Bridge/Junction (`entityType`), as in
the domain taxonomy workbooks.

Examples:
- `HR/CoreHR` — EmployeeRole, ContractorRole, AlumniRole, ManagerRole
- `Finance/GeneralLedger` — Account (GL chart of accounts)
- `Sales/CustomerManagement` — Account, CustomerContactRole

A data domain has a data steward responsible for the quality and definitions of
its entities.

## Placement Rules

When deciding where a new entity belongs, follow these rules in order:

### Rule 1 — Single Sub-Domain Home

Every entity has **exactly one** primary sub-domain home. This is its
canonical location and the source of its stewardship. Other models reuse
it by external reference or derivation, never by copying it
(`make check-ownership`).

### Rule 2 — Place by Stewardship, Not by Consumer Count

Place an entity in the sub-domain that *stewards* it (defines, evolves,
governs), not necessarily the sub-domain with the most consumers.

Example: `Customer` is consumed by Sales, Marketing, Customer Service, and
Billing — but is stewarded by Sales (specifically, `Sales/CustomerManagement`).
That's its home; others reference it.

### Rule 3 — Prefer Specificity When Sub-Domains Overlap

When two sub-domains both touch an entity, place it under the more specific
one. Example: an `Onboarding` entity could plausibly live under TA (which
initiates onboarding) or CoreHR (which executes it). Because
CoreHR is the steward, place it there.

### Rule 4 — Cross-Cutting Goes to `_shared/`

Entities used across multiple sub-domains within a root domain go to that
root's `_shared/` folder (e.g., `02_domain/HR/_shared/`).

Entities used across multiple root domains go to the top-level
`02_domain/_shared/` folder.

Example: `LegalEntityReference` (used across HR, Finance, Legal, Sales) belongs
in `02_domain/_shared/` (currently in the migration backlog).

### Rule 5 — Don't Create One-Entity Sub-Domains Speculatively

A sub-domain with only one data domain inside it is acceptable only when
the sub-domain is a real organizational unit. Don't invent sub-domains to
hold a single entity.

### Rule 6 — Enumerations Live on Their Owning Attribute

A closed list of values is an `enum` on the attribute of the entity that
owns it, with value meanings in `valueDefinitions`
([D3](../decisions/0003-enumerations-on-attributes.md)). Industry-standard
code lists are format rules, and taxonomies are data in the Common taxonomy
model ([D11](../decisions/0011-common-taxonomy-model.md)).

## Capabilities Are Documented Separately

Business **capabilities** (e.g., "Customer Management", "Employee Onboarding")
are not directly modeled in the Domain layer. They were documented in
`docs/capabilities/`, which is now in the
[migration backlog](../migration-backlog.md) with their domains; each returns
with its domain. Each capability document lists:

- The data domains it consumes
- The processes that operationalize it
- The primary steward organization

This separation reflects the fact that capabilities are *what the business
does* while data domains are *what information the business maintains*.
A single capability typically consumes multiple data domains; a single
data domain is consumed by multiple capabilities.

## Example: A New Entity Walkthrough

You want to add a `Certification` entity (employee certifications and
training credentials).

1. **What is it?** A formal record of an employee's earned credential.
2. **Who stewards it?** HR — specifically, Learning & Development (if that
   sub-domain exists) or CoreHR (if not).
3. **Place it**: If L&D sub-domain doesn't exist yet, create
   `HR/LearningDevelopment/` (Rule 5 says we don't invent
   speculative sub-domains, but L&D is a real org unit). Otherwise place
   under existing CoreHR.
4. **Which Foundation kind does it specialise?** Likely `Document` (a
   credential certificate is a documented record): `foundationKind: Document`.
5. **References**: a relationship to EmployeeRole for who holds it.

If usage later expands beyond HR (e.g., Finance tracks CFO certifications),
keep it in HR and have Finance reference it.

## Process and Application Layers — Different Organization

The Domain layer is the only layer using this 3-level hierarchy.

- **Process layer** (`src/03_process/`) holds only the core process model,
  in `_core/`. Definitions of specific processes are data, not schemas.
- **Application layer** (`src/04_application/`) is organized by
  **application**, one folder each, with one physical model per target
  technology.

This asymmetry is intentional: Domain has many entities and benefits from
hierarchy; Process and Application have fewer items at each level and stay
flat for simpler navigation.
