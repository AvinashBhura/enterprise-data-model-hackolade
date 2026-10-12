# Contributing to the Enterprise Data Model

## The golden rules

1. **Every change starts with an approved spec.** See [specs/README.md](specs/README.md).
2. **Dependencies point down only.** A model may depend only on models in its own or a lower layer (`make check-layers`).
3. **One owner per entity.** Define an entity once; elsewhere, reference or derive it (`make check-ownership`).
4. **Never hand-edit a `.hck.json` file.** Change models in Hackolade Studio or with the Hackolade CLI.
5. **No upstream pollution from Application.** Vendor- and platform-specific detail stays in the Application layer.

## Setting up

```bash
make install                  # PyYAML for the checks
make hackolade-config         # dry run: what would be installed into ~/.hackolade/options
make hackolade-config FORCE=1 # install EDM custom properties (backs up existing files), then restart Studio
```

Set the naming conventions that `make hackolade-config` prints, once, in
Tools > Options > Naming Conventions.

## Approval by layer

| Layer | Approval needed | Notes |
| --- | --- | --- |
| Foundation | EDM steering committee | Rare. Check against the seven Foundation principles. Removed attributes are deprecated over at least two releases; breaking changes bump the major version |
| Common | Two domain stewards | Must pass the Reusability Test. Value types only; no reference data |
| Domain | The domain's steward | Entities specialise exactly one Foundation kind. Enums sit on the owning attribute |
| Process, Application | The owner of the model | Process definitions are versioned. Application models keep their derivation links; every deviation has a `deviationReason` |

## Pull request checklist

- [ ] The pull request title names an approved spec: `[NNNN] ...`.
- [ ] Model files were saved by Hackolade Studio (not edited by hand).
- [ ] `make check` passes.
- [ ] `make test` passes.
- [ ] Every new entity and attribute has a description, and every entity has `layer`, `foundationKind`, `entityType` and `steward`.
- [ ] Enum values use SCREAMING_SNAKE_CASE; their meanings are in `valueDefinitions`.
- [ ] READMEs are updated in any folder whose purpose changed.
- [ ] CHANGELOG entry added under "Unreleased".

## Naming conventions

The checks enforce these from `config/edm-rules.yaml`:

- **Entities**: PascalCase, singular (`Person`, `EmployeeRole`, `JobRequisition`).
- **Attributes**: `snake_case` (`hire_date`, `employing_organization`).
- **Technical names**: `snake_case`, at most 63 characters, never a PostgreSQL reserved word. Produced by Hackolade's naming conventions.
- **Enum values**: `SCREAMING_SNAKE_CASE` (`EMPLOYEE`, `FULL_TIME`).
- **Model files**: `<Subdomain>.hck.json` in the Domain layer; `<Application>-<Target>.hck.json` in the Application layer.

## Review cadence

- Architecture review: monthly.
- Domain-steward office hours: weekly per domain.
- Releases: minor every 6 weeks; major releases planned.
