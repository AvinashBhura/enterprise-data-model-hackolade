# EDM Documentation

This documentation explains the Enterprise Data Model in depth — its
architecture, principles, layers, and the modelling patterns that hold it
together.

## Start here

- **New to the EDM?** Read [architecture/overview.md](architecture/overview.md) — five layers in plain language.
- **Need a principle?** [architecture/principles.md](architecture/principles.md) lists every principle with its caption.
- **Need an operational rule?** [architecture/operational_rules.md](architecture/operational_rules.md).
- **Why is something the way it is?** [decisions/](decisions/README.md) records each architecture decision.
- **Modelling something new?** [patterns/](patterns/) has reusable patterns; start with a [spec](../specs/README.md).
- **Building an application model?** [workflows/greenfield.md](workflows/greenfield.md) or [workflows/brownfield.md](workflows/brownfield.md).
- **Have a Hackolade licence now?** [workflows/studio-verification.md](workflows/studio-verification.md).
- **Loading taxonomy data?** [taxonomies-to-load.md](taxonomies-to-load.md).
- **Looking for something that used to be here?** [migration-backlog.md](migration-backlog.md).

## Documentation map

```text
docs/
├── architecture/
│   ├── overview.md                  # the five layers, in plain language
│   ├── principles.md                # every principle with its caption
│   ├── operational_rules.md         # the enforceable rules and their checks
│   ├── dependency_direction.md      # the One-Way Gate rule
│   ├── data_domain_organization.md  # how the Domain layer is organised
│   └── glossary.md                  # definitions of every concept
│
├── layers/
│   ├── foundation.md                # layman's guide — Foundation layer
│   ├── common.md                    # layman's guide — Common sub-layer
│   ├── domain.md                    # layman's guide — Domain layer
│   ├── process.md                   # layman's guide — Process layer
│   └── application.md               # layman's guide — Application layer
│
├── patterns/
│   ├── role_based_relationships.md
│   ├── lifecycle_modeling.md
│   ├── natural_keys_and_surrogates.md
│   ├── bitemporal_modeling.md
│   ├── polymorphic_references.md
│   └── process_versioning.md
│
├── workflows/
│   ├── greenfield.md                # a new application model, derived from the EDM
│   ├── brownfield.md                # an existing database against the EDM
│   └── studio-verification.md       # what to do in Studio once a licence is available
│
├── decisions/                       # architecture decision records D1–D12
├── taxonomies-to-load.md            # the old taxonomies, handed over as data
└── migration-backlog.md             # content removed in the move to Hackolade
```
