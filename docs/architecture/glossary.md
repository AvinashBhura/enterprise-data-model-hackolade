# EDM Glossary

Definitions of every concept used in the Enterprise Data Model.
`hackolade/glossary/edm-glossary.csv` holds the same terms in the format
Hackolade Studio imports, so model objects can be bound to them.

## Core Concepts

**Application Layer** — Layer 5. Physical data models for specific
applications, derived from Domain and Process models (greenfield) or
reverse-engineered from existing databases (brownfield).

**Base Type** — A reusable set of attributes that entities follow:
`Entity`, `Identifiable`, `Lifecycleable`, `Addressable`, `RoleHolder`,
`Classifiable`, `Temporal`. Each entity declares the attributes itself and
lists the base types it follows in `edmComposes`; the contract for each is
in `config/edm-rules.yaml` (decision D2).

**Capability** — *What* the business can do. A noun-phrase. Modeled in
the Domain layer. Distinct from Process (*how* it's executed).

**Classification** — The placement of a business record under a node
of a taxonomy. Recorded, with its history, in `transaction_hierarchy`
(decision D11).

**Common Sub-Layer** — Nested under Foundation. Holds reusable
construction material: composite value types and the generic taxonomy
model.

**Domain Layer** — Layer 3. Capability-aligned stable nouns. Each
business function (HR, Finance, Sales, etc.) owns its piece, one model
per subdomain.

**EDM** — Enterprise Data Model. This project.

**Entity** — The semantic anchor of the EDM: every Foundation concept is
an Entity and carries `entity_id`.

**Entity ID** — The globally unique surrogate identifier (UUID) every
Entity carries. Stable across all systems, reorganizations, integrations.

**Enumeration** — A closed list of allowed values, held as an `enum` on
the attribute that uses it (decision D3). Examples: lifecycle states,
role types.

**Foundation Layer** — Layer 1. Permanent enterprise concepts:
Person, Organization (LegalEntity, OrganizationalUnit), Team, Role,
Activity, Agreement, Asset, Address, Document, Period.

**Natural Identifier** — A business key (e.g., employee_number,
tax_id, vendor_number). Lives on canonical entities via `Identifiable`
when enterprise-issued, or in application models when vendor-issued.

**Polymorphic Reference** — A reference that may point to more than one
kind of entity, held as a pair `<name>_entity_type` + `<name>_entity_id`
with no relationship. The allowed types are listed in
`config/edm-rules.yaml`.

**Process Definition** — A versioned workflow specification. Multiple
versions may coexist; instances bind to a single version for life.

**Process Instance** — A live execution of a Process Definition. Bound
immutably to a single definition version (Frozen-Contract principle).

**Process Layer** — Layer 4. Workflows and instances. References Domain
entities; never modifies them (Borrower principle).

**Reference Data** — The values of a code list or taxonomy (countries,
currencies, job families). Data, not schema: the EDM stores the rules for
these values, never the values themselves.

**Role** — A time-bound engagement of a Person or Organization with
another party. The universal pivot for "who plays what with whom"
relationships. Specialized in Domain (EmployeeRole, Candidate, etc.).

**Source-System Reference** — Pattern in Application layer: every
application record that mirrors an entity owned elsewhere records its
source system and source id.

**Subject Entity** — The Domain-layer entity a ProcessInstance
operates on. Captured by `subject_entity_id` + `subject_entity_type`.

**Surrogate Key** — System-generated identifier (UUID) that never
changes. Distinct from natural keys (business identifiers that may
change). Both coexist in the EDM.

**Taxonomy** — A hierarchical classification (categories and their
containment). Stored as data in the Common taxonomy model, with full
version history (decision D11).

**Transaction Hierarchy** — The append-only record of which taxonomy
node a business record was classified under, when, and with which paths.
"Transaction" here means any classified business record, not a financial
transaction.

**Value Type** — A self-contained composite value structure with no
independent identity, reused by external reference. Examples:
`AmountType` (value + currency), `QuantityType` (value + unit),
`DocumentType`, `StateTransition`, `NaturalIdentifier`.

## Hackolade Concepts

**Custom Property** — EDM metadata stored on a model object (for example
`foundationKind`, `entityType`, `steward`). Configured in
`hackolade/customProperties/` and checked by `tools/`.

**Derivation** — Creating a model from one or more polyglot models
(`polyglotDerive`). The parent stays the master; the derived model keeps
local changes as deviations and is refreshed with `polyglotUpdate`.

**Deviation** — A local change a derived model makes to an entity it
inherited. Deviations on entities derived from Foundation or Common are not
allowed; others need a `deviationReason`.

**External Reference** — Reuse of an entity, attribute or definition from
another model file by relative path. Read-only in the model that uses it;
refreshed with `extRefUpdate`.

**Model Definition** — A reusable structure inside one model. Not used by
the EDM yet: shared value types are entities in `CommonValueTypes`, marked
`edmValueType` (D12).

**Physical Model** — A model for one target technology (for example
PostgreSQL), from which Hackolade generates DDL.

**Polyglot Model** — A technology-neutral logical model. Foundation,
Common, Domain and Process models are polyglot models.

**Supertype Group** — Hackolade's inheritance construct: a supertype, its
subtypes, and the strategy that decides how inheritance becomes tables. Until
Studio verification (D12), entities carry their Foundation kind's attributes
instead, the shape the roll-down strategy produces.

## Lifecycle Concepts

**Lifecycle State** — Coarse entity-level state (Active, Inactive,
Archived, etc.). Lives on entities via the `Lifecycleable` base type.
Distinct from process workflow state.

**State Transition** — A recorded change from one lifecycle state to
another. Stored in `state_history` on Lifecycleable entities.

**Workflow State** — Fine-grained state managed by ProcessInstance.
Distinct from entity-level lifecycle state.

## Architectural Concepts

**Bounded Context** — A capability's "turf" — the set of entities it
owns and is the primary steward for. One polyglot model per bounded
context.

**Borrower Principle** — Process references Domain; Process never
modifies Domain.

**Capability-Centricity** — Domain models capabilities (what the
business is) rather than processes (how it runs).

**Frozen-Contract** — A ProcessInstance's binding to a definition
version is set at instance creation and never changes.

**Highlander Principle** — There can be only one. Each concept
exists once across the enterprise.

**One-Way Gate** — Dependencies flow upward only. Foundation knows
nothing of Application.

**Operational Rule** — An enforceable constraint backed by tooling
and tests. Distinct from a principle (aspirational).

**Primary Stewardship** — Each Domain entity has exactly one
primary-steward capability that owns it.

**Reusability Test** — Before placing anything in Common, ask:
"Would another enterprise with a different business need this?"

**Role Immutability** — Roles do not mutate core terms. Changes end
one Role and begin another, preserving history.

**Single Owner Principle** — See Primary Stewardship.

**Snapshot Principle** — Every ProcessDefinition is versioned;
instances bind to a snapshot.
