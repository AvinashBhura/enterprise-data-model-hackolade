# Layman's Guide — Application Layer

## What it is in one sentence

The physical data models of individual applications — tables, columns,
keys and vendor-specific fields for one database technology — derived from
or mapped to the Domain and Process models.

## Why it matters

Workday, ServiceNow, Salesforce and SAP each have their own representation
of "an employee", with their own identifiers and field names. If you let
those vendor quirks creep up into Domain, Domain stops being canonical — it
becomes Workday's shape wearing a disguise.

The Application layer gives each application its own space. The Workday
worker ID and Workday's supervisory organisation live in the Workday model;
the ServiceNow user reference lives in the ServiceNow model. Neither touches
the clean Domain `EmployeeRole`.

## Two ways in

**Greenfield — a new application.** Derive its physical model from the
Domain and Process polyglot models it needs (`polyglotDerive`), then add
the physical design: keys, indexes, technical names, application-only
tables. Every local change is a tracked deviation with a `deviationReason`,
and the derivation link keeps traceability back to the Domain.

**Brownfield — an existing application.** Reverse-engineer its database
into a physical model, map tables and columns to Domain concepts (glossary
terms and the `edmMapsTo` property), compare with an EDM-ideal model
derived from the Domain, and refactor where it pays.

Both workflows are specified in
[spec 0005](../../specs/0005-candidate-journey/spec.md).

## A real-world example

When your company migrates from Workday to a new HR system:
1. Foundation: **no change**.
2. Common, Domain, Process: **no change**.
3. Application: the Workday folder retires; a new folder appears.

If a vendor migration forces Domain changes, the architecture is
leaking. The Application layer is what keeps that leak sealed.

## What lives here

| Folder | Holds |
|---|---|
| `_shared/` | `ApplicationShared.hck.json`: SourceSystemReference and SyncMetadata, which application models derive from |
| `<Application>/` | `<Application>-<Target>.hck.json`, one physical model per target technology |

The first application model is the Candidate Journey for PostgreSQL. Entities
an application uses but does not own are kept as an id plus a source-system
reference, not as copied tables.

## Why this layer is allowed to change constantly

Application-layer volatility is **expected and healthy**. Vendors change
schemas. Integrations add fields. The Application layer absorbs all of that,
leaving everything underneath stable.

## The Application principles

1. **Extender** — Add fields to the canonical shape; never change its meaning.
2. **Shapeshifter** — Changes at the pace of the software that produces the data.
3. **Fingerprint** — Every application record that mirrors an entity owned elsewhere names its source system.
4. **Contract** — Every application model documents how it maps to the Domain.
5. **One-Way Gate** — Foundation, Common, Domain and Process never depend on Application.

## Adding a new application

1. Write a spec ([specs/README.md](../../specs/README.md)).
2. Create `04_application/<Application>/` with a README.
3. Derive (greenfield) or reverse-engineer (brownfield) its physical model.
4. Keep vendor-specific natural keys and fields here, never in Domain.
5. Give every deviation a `deviationReason`; run `make check`.
6. **Never change a model outside `04_application/`** for an application's sake.

## See also

- Application principles: [principles.md](../architecture/principles.md)
