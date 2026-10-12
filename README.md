# Enterprise Data Model (EDM)

A layered Enterprise Data Model, built in [Hackolade Studio](https://hackolade.com/),
for a "model once, use everywhere" approach: one stable, canonical
representation of enterprise concepts that every system, report and
integration can rely on.

The EDM is a **schema store**. It holds models and the rules that govern
them; it holds no reference data and no instance data.

> **Status: moved to Hackolade, awaiting Studio verification.** Every model
> for Common, Foundation, HR, the core process model and the Candidate
> Journey application is in `src/` (specs 0002–0005). They were written by a
> one-time builder before a Hackolade licence was available
> ([D12](docs/decisions/0012-complete-without-studio.md)); the
> [verification runbook](docs/workflows/studio-verification.md) is the next
> step. The LinkML EDM stays in its own repository,
> [AvinashBhura/enterprise-data-model](https://github.com/AvinashBhura/enterprise-data-model),
> where tag `linkml-final-v0.5.0` is its last version
> ([D13](docs/decisions/0013-separate-hackolade-repository.md)); see
> [docs/migration-backlog.md](docs/migration-backlog.md).

## Quick start

```bash
make install            # install PyYAML (the only dependency of the checks)
make check              # run all governance checks
make test               # test the checks
make hackolade-config   # see which Hackolade settings would be installed
make help               # every command
```

Model files (`.hck.json`) are opened, changed and saved in Hackolade Studio,
or changed with the Hackolade CLI. Never edit them by hand.

## Architecture

Five layers, from most stable (bottom) to most volatile (top). Dependencies
point **down only**:

```text
┌────────────────────────────────────────────────────────────┐
│ 5. APPLICATION   physical models per application           │
├────────────────────────────────────────────────────────────┤
│ 4. PROCESS       workflow definitions and instances        │
├────────────────────────────────────────────────────────────┤
│ 3. DOMAIN        capability-aligned stable nouns           │
├────────────────────────────────────────────────────────────┤
│ 2. COMMON        shared value types, taxonomy model        │
│   (nested inside Foundation)                               │
├────────────────────────────────────────────────────────────┤
│ 1. FOUNDATION    permanent enterprise concepts             │
└────────────────────────────────────────────────────────────┘
```

Foundation, Common, Domain and Process are Hackolade **polyglot**
(technology-neutral) models. Application models are **physical** models,
derived from them for a target such as PostgreSQL. Hackolade generates DDL,
JSON Schema and documentation from the models
([D4](docs/decisions/0004-generation-by-hackolade.md)).

## Repository layout

```text
enterprise-data-model/
├── src/                   # model files, one folder per layer (see src/README.md)
│   ├── 01_foundation/     #   Foundation; common/ = Common sub-layer
│   ├── 02_domain/         #   <Domain>/<Subdomain>/<Subdomain>.hck.json
│   ├── 03_process/        #   _core/ = the core process model
│   └── 04_application/    #   <Application>/<Application>-<Target>.hck.json
├── config/edm-rules.yaml  # every rule the checks apply
├── tools/                 # Python governance checks (read-only on models)
├── tests/                 # tests for the checks
├── hackolade/             # Hackolade settings in Git: custom properties, naming, glossary
├── specs/                 # spec-driven development: every change starts here
├── docs/                  # architecture, layers, patterns, decisions, migration backlog
└── ci/                    # Hackolade CLI image for CI (spec 0006)
```

## How changes are made

1. Write a spec in `specs/` and get it approved ([specs/README.md](specs/README.md)).
2. Make the change in Hackolade Studio on a branch; save the model files.
3. Run `make check` and `make test`.
4. Open a pull request naming the spec, for example `[0003] Talent Acquisition model`.

Architecture decisions are recorded in [docs/decisions/](docs/decisions/README.md).

## Layer principles

| Layer | Principle captions |
|---|---|
| **Foundation** | Highlander · Boring · Independence · Common Language · Spartan · Noun · Origin |
| **Common** | One-Meaning · Shared-Shelf · Rosetta · Scaffolding · Clean-Contract |
| **Domain** | Inheritance · What-Not-How · Fence · Thing · Who-Plays-What · Single Owner |
| **Process** | Borrower · Snapshot · Ledger · Frozen-Contract |
| **Application** | Extender · Shapeshifter · Fingerprint · Contract · One-Way Gate |

Full explanations in [docs/architecture/principles.md](docs/architecture/principles.md).

## Operational rules

1. **Role Immutability** — Roles don't mutate core terms. Changes end one Role and start another.
2. **Natural Key Placement** — Enterprise-native keys on canonical entities via `Identifiable`; vendor keys in application models.
3. **Domain Primary Stewardship** — Each entity is defined in one model, owned by its primary-steward domain (`make check-ownership`).
4. **Process Binding Immutability** — Instance-to-definition bindings are set at birth, never changed.
5. **Schema, not reference data** — Closed lists are enums on attributes; code lists are format rules; taxonomies are data in the Common taxonomy model ([D3](docs/decisions/0003-enumerations-on-attributes.md), [D11](docs/decisions/0011-common-taxonomy-model.md)).

## Key modelling decisions

- **Every Foundation concept carries `entity_id`**, a stable surrogate key.
- **Employee is a Role, not a Person subtype.** A Person can hold several Roles at once and over time.
- **Team is independent**, not an Organization subtype.
- **Process is a separate layer** from Domain. Process references Domain; it never changes it.
- **The Application layer isolates vendor and platform detail**, so changes there do not ripple down.
- **No Party supertype.** Person + Organization + Role; relationships are carried by a Role, a junction entity, or a typed reference.

## Prerequisites

- Hackolade Studio 8.13 or later (Workgroup edition for in-tool Git), with the PostgreSQL plugin ([D9](docs/decisions/0009-licences-and-version.md)).
- Python 3.10 or later, for the checks.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Apache License 2.0 — see [LICENSE](LICENSE).
