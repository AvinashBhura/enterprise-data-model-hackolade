# Operational Rules

Five enforceable rules that turn the principles into concrete behaviors.
Rules a schema can show are checked by `make check`. Rules about how data
changes at run time are enforced by the applications that write the data,
and reviewed in pull requests.

## Rule 1 — Role Immutability

> Roles do not mutate their core terms once effective. Changes to
> `employing_organization`, `primary_position`, or `employment_type`
> end the current Role (set `effective_to`) and begin a new one.

**Why:** preserves accurate history. A reorg or position change is
a new engagement, not an edit. A single Person may accumulate dozens
of Role records over a career — that is correct, not bloat.

**Anti-pattern:** mutating `employing_organization` on an existing
EmployeeRole when an employee transfers between divisions. The
correct action is to end the existing Role and create a new one.

**Enforced by:** review, and the applications that write Role data (a schema cannot show a mutation).

## Rule 2 — Natural Key Placement

> Enterprise-native natural keys live on canonical entities via
> `Identifiable.natural_identifiers`. Vendor system keys live ONLY on
> Application-layer models.

**Why:** keeps Domain vendor-neutral. When a vendor system migrates,
Domain entities stay unchanged.

**Anti-pattern:** adding `workday_worker_id` as an attribute on the
canonical `EmployeeRole` in `02_domain/HR/`. The correct location is the
Workday application model in `04_application/Workday/`.

**Enforced by:** review (a check would need to know every vendor's key names).

## Rule 3 — Domain Primary Stewardship

> Every Domain entity has a single primary-steward capability and lives
> in that capability's folder. Cross-cutting entities with no single
> steward live in `02_domain/_shared/`. Specific instances (e.g., Acme's
> actual Engineering Division) are master data, not part of `src/`.

**Why:** clear ownership. No replication of similar entities across
capabilities.

**Anti-pattern:** defining `Position` in both `HR/` and `Sales/`
because both use it. Sales should reference HR's `Position`.

**Enforced by:** `make check-ownership` (each entity is defined in one model) and `make check-layers`.

## Rule 4 — Process Binding Immutability

> A ProcessInstance's binding to a ProcessDefinition is set at instance
> creation and NEVER changes. Process migrations are modeled as
> termination of the old instance (state → MIGRATED) and creation of
> a new instance with explicitly carried-over state.

**Why:** reproducibility and audit. An instance's behavior must always
be explainable by reference to a single, immutable definition version.

**Anti-pattern:** updating an existing ProcessInstance's `definition`
from v3.2 to v4.0 mid-flight.

**Enforced by:** the applications that write process instances. The rule is stated on `ProcessInstance.definition` (spec 0004).

## Rule 5 — Schema, Not Reference Data

> - **Closed lists** (lifecycle states, types) are an `enum` on the
>   attribute of the entity that owns them.
> - **Standard code lists** (currency, country, language, unit) are a
>   format rule on the attribute; their values are reference data, kept
>   outside the EDM.
> - **Taxonomies** are data in the Common taxonomy model.
> - **Instance data** (specific records like Acme's actual divisions) is
>   master data — never in `src/`.

**Why:** the EDM is a schema store. Values change on their own schedule and
have their own owners; schemas should not have to change with them
([D3](../decisions/0003-enumerations-on-attributes.md),
[D11](../decisions/0011-common-taxonomy-model.md)).

**Anti-pattern:** writing Acme's departments into a model as an `enum`.
Organisation types are a taxonomy (data); Acme's divisions are HR master
data.

**Enforced by:** `make check-enums` (closed lists stay consistent) and review.

---

## Enforcement Summary

| Rule | How it is enforced |
|---|---|
| Role Immutability | Review; applications that write Role data |
| Natural Key Placement | Review |
| Domain Stewardship | `make check-ownership`, `make check-layers` |
| Process Binding Immutability | Applications that write process instances |
| Schema, Not Reference Data | `make check-enums`; review |

Structural rules are checked too: the Strict-Foundation rule
(`make check-foundation-kind`), base-type contracts (`make check-base-types`),
junction shape (`make check-junctions`), polymorphic references
(`make check-references`) and deviations in derived models
(`make check-deviations`). See [tools/README.md](../../tools/README.md).
