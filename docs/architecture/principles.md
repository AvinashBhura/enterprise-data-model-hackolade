# EDM Principles — Complete Reference

Twenty-seven principles, organized by layer. Each principle has a
**mnemonic caption** that makes it teachable in one phrase.

---

## Foundation Layer (7)

| # | Principle | Caption | Meaning |
|---|---|---|---|
| 1 | Universality | **The Highlander Principle** | "There can be only one." Each concept exists once across the enterprise. |
| 2 | Structural Immutability | **The Boring Principle** | "If it's changing, it doesn't belong here." Foundation changes are rare. |
| 3 | Abstraction | **The Independence Principle** | "Exists without the business needing to do anything." |
| 4 | Semantic Integrity | **The Common Language Principle** | "One meaning, understood by everyone." Neutral enterprise terminology. |
| 5 | Minimalism | **The Spartan Principle** | "Only concrete entities live here — nothing else earns a seat." |
| 6 | Entity-Purity | **The Noun Principle** | "The business is made of things, not construction material." |
| 7 | Semantic Anchoring | **The Origin Principle** | "Entity is where things begin, not what they must become." Strict form: **only Foundation entities inherit directly from Entity**; every Domain/Process/Application entity specializes a specific Foundation kind. |

## Common Sub-Layer (5)

| # | Principle | Caption | Meaning |
|---|---|---|---|
| 1 | Non-Ambiguity | **The One-Meaning Principle** | "A value means the same thing wherever it appears." |
| 2 | Reusability | **The Shared-Shelf Principle** | "Built once, pulled down by many." |
| 3 | External Mapping | **The Rosetta Principle** | "Speaks fluent Schema.org, SKOS, and ISO." |
| 4 | Supportive, Not Substantive | **The Scaffolding Principle** | "Holds up the building; isn't the building." |
| 5 | Non-Overlap | **The Clean-Contract Principle** | "No two base types claim the same attribute." |

## Domain Layer (6)

| # | Principle | Caption | Meaning |
|---|---|---|---|
| 1 | Specialization | **The Inheritance Principle** | "Extend what Foundation gives; never redefine it." |
| 2 | Capability-Centricity | **The What-Not-How Principle** | "Model what the business is; let Process handle how it runs." |
| 3 | Bounded Context | **The Fence Principle** | "A domain owns its turf; neighbors reference, not reach in." |
| 4 | Noun-Orientation | **The Thing Principle** | "Domain entities are things, not verbs or states." |
| 5 | Role-Based Relationships | **The Who-Plays-What Principle** | "Relationships are Roles, not class hierarchies." |
| 6 | Primary Stewardship | **The Single Owner Principle** | "Every entity lives with its primary steward, not replicated across domains." |

## Process Layer (4)

| # | Principle | Caption | Meaning |
|---|---|---|---|
| 1 | Consumption, Not Redefinition | **The Borrower Principle** | "Process uses Domain; Process never edits Domain." |
| 2 | Versionability | **The Snapshot Principle** | "Every process definition is versioned; instances bind to a snapshot." |
| 3 | Event-Orientation | **The Ledger Principle** | "State lives in events; events point to domain entities." |
| 4 | Binding Immutability | **The Frozen-Contract Principle** | "An instance's definition binding is set at birth and never changes." |

## Application Layer (5)

| # | Principle | Caption | Meaning |
|---|---|---|---|
| 1 | Inheritance-Only Extension | **The Extender Principle** | "Add fields to the canonical shape; never change its meaning." |
| 2 | Adaptability | **The Shapeshifter Principle** | "Changes at the pace of the software that produces the data." |
| 3 | Source-System Transparency | **The Fingerprint Principle** | "Every Application entity names its source system." |
| 4 | Bidirectional Mapping | **The Contract Principle** | "Every projection documents its transformation to and from the canonical shape." |
| 5 | No Upstream Pollution | **The One-Way Gate Principle** | "Foundation, Common, Domain, and Process never depend on Application." |
| 6 | Strict-Foundation Anchoring | **The Closed-Ontology Rule** | "Only Foundation entities directly specialize Entity. Domain, Process, and Application entities must specialize a specific Foundation kind." |
| 7 | Typed Cross-Entity References | **The No-Loose-Strings Rule** | "Every reference from one EDM entity to another is a typed relationship to the target entity. Loose `entity_id` values are allowed only as polymorphic pairs (`<name>_entity_type` + `<name>_entity_id`) at generic levels, each listed in `config/edm-rules.yaml` and checked by `make check-references` (e.g., `ProcessInstance.subject_entity_id`)." |

---

## At a Glance

**Stability gradient (bottom → top)**
Foundation = decades · Common = years · Domain = years · Process = quarters · Application = sprints.

**Each layer's job**
- Foundation: declares what enterprise things ARE
- Common: provides the building blocks
- Domain: declares what each capability HAS
- Process: declares how each capability RUNS
- Application: declares how each system STORES it

**The dependency direction**
Each layer depends only on the layers below it. Never the reverse.

---

## How the principles are enforced

| Principle | Enforced by |
|---|---|
| One-Way Gate, dependency direction | `make check-layers`, `make check-cycles` |
| Origin / Closed-Ontology (Strict-Foundation) | `make check-foundation-kind`, `make check-foundation-contract` |
| Inheritance (extend, never redefine) | `make check-foundation-contract`, `make check-deviations` |
| Single Owner, Highlander | `make check-ownership` |
| Clean-Contract (base types) | `make check-base-types` |
| One-Meaning (same list, same values) | `make check-enums` |
| No-Loose-Strings | relationships in the models; `make check-references` for the allowed pairs |
| Who-Plays-What (junctions) | `make check-junctions` |
| Common Language | `make check-naming`, `make check-metadata`, the glossary in `hackolade/glossary/` |
| Borrower, Frozen-Contract, Ledger | the core process model's structure; reviews (`model-reviewer` agent) |
| Extender, Fingerprint, Contract | derived application models; `make check-deviations`; `source_system_reference` |

Principles a check cannot see are covered in review: the `model-reviewer`
agent refers to this page.
