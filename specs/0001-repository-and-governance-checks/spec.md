# 0001 — Repository structure and governance checks

Status: Implemented (2026-10-12), amended for D12 and D13
Owner: EDM architecture
Decisions: [D4](../../docs/decisions/0004-generation-by-hackolade.md), [D6](../../docs/decisions/0006-migration-scope.md), [D9](../../docs/decisions/0009-licences-and-version.md), [D12](../../docs/decisions/0012-complete-without-studio.md)
Depends on: none (first spec)

## Problem

The repository is built around LinkML: YAML schemas, LinkML generators, LinkML
validation and LinkML-specific checks. The EDM is moving to Hackolade. The
repository needs a Hackolade-shaped layout and Python checks that read Hackolade
model files, before any model is migrated.

## Scope

In scope:
- New folder layout, keeping the numbered layer folders.
- Removal of LinkML files, generators, config and LinkML-only tests.
- `config/edm-rules.yaml` and the Python checks that read it.
- Tests for the checks.
- Makefile targets, `pyproject.toml`, README files per folder, core docs.

Out of scope:
- Migrating any model (specs 0002–0005).
- CI workflow and AI assets (spec 0006).

## Requirements

### Layout

1. The repository follows this layout:

   ```text
   hackolade/            customProperties/Polyglot/, naming/, glossary/
   src/01_foundation/    Foundation.hck.json; common/
   src/02_domain/        _shared/; one folder per domain; one folder per subdomain
   src/03_process/       _core/
   src/04_application/   _shared/; one folder per application
   config/               edm-rules.yaml
   tools/                Python checks (read model files, never write them)
   tests/                tests for the checks, with small fixture models
   specs/                spec-driven development
   docs/                 architecture, layers, conventions, workflows, decisions
   ci/                   Dockerfile and compose file for the Hackolade CLI
   ```

2. Every folder that holds models, and `tools/`, `config/`, `hackolade/`, `specs/`, has a README saying what lives there, who owns it, and what it may depend on.

### Retirement of LinkML assets

3. Before anything is removed, `main` is tagged `linkml-final-v0.5.0`. All frozen and retired LinkML content stays recoverable from this tag.
4. Removed: `linkml-config.yaml`, `generators/`, `examples/` (LinkML instance data), all `*.yaml` schemas under `src/`, `tools/validate_all.py`, `tools/lint_yaml.py`, `tests/validation/`, and LinkML dependencies in `pyproject.toml`.
5. Non-HR domains (Facilities, Finance, Governance, IT, Legal, Procurement, Sales, Security), the 7 sample processes and the 5 sample application models are removed from the tree, not converted. `docs/migration-backlog.md` lists each one with its path at the tag, so each can be migrated later under its own spec.
6. Docs that describe architecture and principles are kept and edited to remove LinkML terms: `docs/architecture/*`, `docs/layers/*`, `docs/patterns/*`. `docs/capabilities/*` moves to the migration backlog with its domains.

### Rules file

7. `config/edm-rules.yaml` holds every configurable rule, so rules change without code changes:
   - layer order and the folder that defines each layer;
   - allowed dependency directions (a `_shared` folder belongs to the layer that contains it; within the Domain layer, a subdomain may reference entities owned by any other subdomain, in its own domain or another, as long as no cycle forms);
   - naming rules for business names and technical names (pattern, case, reserved words, abbreviation file);
   - required custom properties per object level;
   - the allowed values for `foundationKind`, `entityType` and `layer`;
   - base-type contracts (D2): for each base type, its attribute names, types, required flags and descriptions;
   - intended enum differences (D3): attribute names allowed to carry different value lists;
   - allowed targets for polymorphic references and for `transaction_hierarchy` (spec 0002);
   - the deviation policy for derived models;
   - the supported Hackolade persistence schema versions and the pinned Studio version.

### Checks

8. Each check is a separate command under `tools/`, reads only `.hck.json` files and the rules file, and exits non-zero on any violation with a message naming the file, object and rule.

   | Check | Rule |
   | --- | --- |
   | `check_layers` | A model depends only on models in its own or a lower layer. Dependencies are read from `polyglotModelPaths` (derivation parents) and the `link` of each external definition |
   | `check_cycles` | No cycle in the dependency graph, transitive included |
   | `check_naming` | Business and technical names follow the configured rules |
   | `check_metadata` | Every entity has `layer`, `foundationKind`, `entityType`, `steward` and a description; values are from the allowed lists |
   | `check_foundation_kind` | Every Domain, Process and Application entity specialises exactly one Foundation kind (the Strict-Foundation rule) |
   | `check_base_types` | An entity listing a base type in `edmComposes` carries that base type's attributes exactly as the contract says |
   | `check_enums` | The same attribute name carries the same `enum` values everywhere, unless listed as an intended difference |
   | `check_junctions` | An entity with `entityType: Bridge/Junction` has its own key and exactly two relationships to the entities it connects |
   | `check_references` | Polymorphic reference pairs and `transaction_hierarchy` targets name entity types that exist in the EDM |
   | `check_deviations` | No local deviation on entities derived from the Foundation; other deviations carry a reason in `deviationReason` |
   | `check_format` | Each model file has a supported persistence schema version and was saved by the pinned Studio version or later |
   | `check_ownership` | Each entity is defined (not referenced or derived) in exactly one model across the repository |

9. `make check` runs all checks. Each also runs alone, for example `make check-layers`.
10. Checks use only the Python standard library plus PyYAML. Python 3.10 or later. Tests use the standard `unittest` module.

### Hackolade settings in Git

11. `hackolade/customProperties/Polyglot/` holds the EDM custom property configuration (entity level: `layer`, `foundationKind`, `entityType`, `steward`, `edmComposes`, `sourceTaxonomyRef`; attribute level: `valueDefinitions`, `dataClassification`, `edmMapsTo`; model level: `edmLayer`, `edmDomain`; derived models: `deviationReason`).
12. `make hackolade-config` copies these settings and the abbreviation file into the user's Hackolade options folder (`~/.hackolade/options`), after backing up what is there, and prints the naming-convention settings to set by hand (see resolved question 2). It prints what it changed.

## Acceptance criteria

1. Tag `linkml-final-v0.5.0` exists on the commit before removal. Checked with `git tag`.
2. No file under `src/`, `tools/` or `tests/` mentions LinkML, and `pyproject.toml` has no LinkML dependency. Checked with `grep -ri linkml src tools tests pyproject.toml` returning nothing.
3. `docs/migration-backlog.md` lists every removed domain, process and application folder with its path at the tag. Checked by review against `git ls-tree linkml-final-v0.5.0 src`.
4. Each check in requirement 8 has at least one passing and one failing fixture test. `make test` passes.
5. `make check` passes on an empty `src/` tree and fails on each failing fixture.
6. Every folder named in requirement 2 has a README. Checked by a test.
7. `make hackolade-config` on a machine with existing Hackolade options creates a backup and copies the settings. Checked once by hand.

## Validation

```bash
make test
make check
git tag --list 'linkml-final-*'
grep -ri linkml src tools tests pyproject.toml || echo "clean"
```

## Resolved questions

Approved by Avinash Bhura on 2026-10-12 with the recommended answers.

1. `make hackolade-config` is a dry run by default: it lists what would change in the user's Hackolade options folder. `make hackolade-config FORCE=1` backs up the existing settings and applies the change.
2. Hackolade does not document the file in which it stores naming-convention settings. `make hackolade-config` therefore installs the custom properties and the abbreviation file, and prints the naming settings to set once in Tools > Options > Naming Conventions. When a modeller has saved those settings, the settings file is captured into `hackolade/naming/` under a follow-up change to this spec.
3. Python 3.10 or later (requirement 10), so the checks run on the default Python of current Ubuntu LTS images.
4. Until spec 0006 replaces it, `.github/workflows/validate.yml` runs `make test` and `make check` instead of the LinkML steps, so CI stays green.

## Amendments — 2026-10-12, decision [D12](../../docs/decisions/0012-complete-without-studio.md)

Made while completing specs 0002–0006 without a Hackolade licence. They change requirements 8 and 11 as follows.

1. New check `check_foundation_contract` (`make check-foundation-contract`): every Domain, Process and Application entity carries the attributes of its Foundation kind as `Foundation.hck.json` defines them; inside the Foundation, LegalEntity and OrganizationalUnit carry Organization's. Allowed changes are configured in `foundation_contract` in `config/edm-rules.yaml`.
2. `check_junctions`: a junction names the two entities it connects in the custom property `edmConnects`, has a relationship to each, and has its own key. Further relationships (for example `held_by_person`, carried from Role) are allowed.
3. `check_references`: a rule on a Foundation kind also applies to every entity that specialises it (`foundationKind`, and `foundation.subkinds`).
4. `check_foundation_kind`: entities in `foundation.technical_paths` (`src/04_application/_shared/`) may use `none`.
5. `check_deviations`: in a physical model, a change of physical data type (`deviations.physical_type_keys`) is allowed on entities derived from the Foundation, with a reason.
6. `check_format`: files written by the builder (model property `edmBuiltBy`) are accepted while `format.accept_builder_output` is true. Set it to false when Studio verification is done.
7. `check_base_types`: a contract type may list alternatives (`enum|string`); arrays read their items from `properties`, where Hackolade stores them.
8. Requirement 11: entity custom properties `edmConnects`, `edmValueType` and `edmAbstract` are added, and `hackolade/customProperties/PostgreSQL/` holds the same EDM tab for PostgreSQL models.

## Amendment — 2026-10-12, decision [D13](../../docs/decisions/0013-separate-hackolade-repository.md)

The Hackolade EDM lives in its own repository, `AvinashBhura/enterprise-data-model-hackolade`, started from the state this spec produced. Requirements 3–5 (tag, then remove) apply to the LinkML repository, `AvinashBhura/enterprise-data-model`, which keeps its history and the tag `linkml-final-v0.5.0`. Acceptance criterion 1 is checked there: `git tag --list 'linkml-final-*'` in the local clone of that repository, where the tag is kept.

