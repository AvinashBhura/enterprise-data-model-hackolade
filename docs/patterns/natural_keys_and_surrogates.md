# Pattern — Natural Keys and Surrogates

## The principle

Every Entity carries a **surrogate identifier** (`entity_id`, a UUID)
that never changes. **Natural identifiers** (business keys) are
optional and may be multiple, each scoped to an issuing scheme. The
**placement of natural keys depends on whether they are
enterprise-issued or vendor-issued**.

## The surrogate (entity_id)

Declared on every Foundation concept under the `Entity` contract in
`config/edm-rules.yaml`, and carried by every entity that specialises one:

| Attribute | Type | Rule |
|---|---|---|
| `entity_id` | uuid | Required; the primary key |

Properties:
- Globally unique (UUID v4).
- System-generated at creation; never changes.
- Stable across systems, reorganizations, integrations, vendor migrations.
- The join key for cross-system queries.

The surrogate is what makes integration possible. Different systems
will represent the same Person with different vendor IDs — but the
single Person.entity_id ties them together.

## The natural identifiers

Declared by entities that follow the `Identifiable` base type
([D2](../decisions/0002-base-type-attributes-on-entities.md)):

| Attribute | Type |
|---|---|
| `natural_identifiers` | array of `NaturalIdentifier` |

`NaturalIdentifier` is a value type in Common:

| Attribute | Type | Required |
|---|---|---|
| `value` | string | Yes |
| `scheme` | string | Yes |
| `issuer` | string | No |
| `issued_at` | date | No |
| `valid_from` | date | No |
| `valid_to` | date | No |

A single entity may carry zero, one, or many natural identifiers,
each tagged by the scheme that issued it.

## The placement rule (Operational Rule 2)

> **Enterprise-native** natural keys live on canonical entities via
> `Identifiable.natural_identifiers`.
> **System-of-record vendor** natural keys live ONLY in Application-
> layer models.

**Examples**:

| Identifier | Placement |
|---|---|
| Acme employee_number "E10847" | EmployeeRole.natural_identifiers (enterprise-issued) |
| Workday Worker ID "WD-998234" | Workday application model, `workday_worker_id` column (vendor-issued) |
| Okta User ID "00u3j2nKLuZcq5z7B3a8" | Okta application model, `okta_user_id` column (vendor-issued) |
| ISO country code "US" | Address.country (ISO 3166-1 format rule) |
| Tax ID | LegalEntity.tax_identifier or natural_identifier (depending on use) |

## Why this distinction matters

If you put `workday_worker_id` directly on the canonical EmployeeRole:
- When you migrate from Workday, every EmployeeRole record needs
  schema surgery.
- Domain becomes coupled to vendor presence.
- Multiple vendors can't coexist (which Workday ID is "the" one?).

If `workday_worker_id` lives only in the Workday application model:
- Migrate to a new HRIS by retiring the Workday model and building the new
  system's model. Canonical EmployeeRole unchanged.
- Several vendor models can coexist freely.
- Domain stays vendor-neutral.

## Querying across systems

Every application table that mirrors a canonical entity keeps its
`entity_id`: inherited through derivation from the Domain model
(greenfield), or mapped to it with `edmMapsTo` (brownfield). Vendor keys sit
next to it. To find "the same Person across all systems", join every
application's person table on `entity_id`.

The surrogate `entity_id` is the universal join key.

## Anti-patterns

- Using a natural key as the primary identifier (employee_number can be
  reissued; UUID can't).
- Storing vendor IDs on canonical entities.
- Storing identifiers as bare strings without a scheme tag.
