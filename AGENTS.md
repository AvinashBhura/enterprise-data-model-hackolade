# AGENTS.md — instructions for AI coding agents

This is the one instruction file for every AI agent working in this repository
(Claude Code, GitHub Copilot, Codex). Tool-specific files only point here.

## What this repository is

An Enterprise Data Model (EDM) kept as Hackolade models (`.hck.json`), with
Python governance checks. The value is in the layers and their rules; the
entities follow from them. Read [README.md](README.md) and
[docs/architecture/overview.md](docs/architecture/overview.md) first.

## Layers and the dependency rule

| Rank | Layer | Folder | Holds |
| --- | --- | --- | --- |
| 0 | Common | `src/01_foundation/common/` | Shared value types; the generic taxonomy model |
| 1 | Foundation | `src/01_foundation/` | Entity and the 11 Foundation concepts |
| 2 | Domain | `src/02_domain/<Domain>/<Subdomain>/` | One polyglot model per subdomain |
| 3 | Process | `src/03_process/_core/` | The core process model |
| 4 | Application | `src/04_application/<App>/` | Physical models |

A model may depend only on models of the same or a lower rank, with no cycles.
Dependencies are derivation links and external references.

## Hard rules

1. **Strict-Foundation rule.** Every Domain, Process and Application entity
   specialises exactly one Foundation kind (`foundationKind`) and carries that
   kind's attributes as `Foundation.hck.json` defines them (D12).
2. **Single owner.** Each entity is defined in one model. Others derive it
   (read-only copy) or reference it; never copy and edit.
3. **Workflow state lives in the Process layer**, never on Domain entities.
4. **Never hand-edit `.hck.json` files.** Change models in Hackolade Studio or
   with the Hackolade CLI. The file format is not a published contract.
5. **No change without an Approved spec** (`specs/`). A pull request that
   changes `src/`, `tools/`, `config/` or `hackolade/` names its spec as
   `[NNNN]` in the title.

## Decisions in one line each

- **D2** Base-type attributes (Identifiable, Lifecycleable, Temporal, Addressable) are declared on each entity; contracts live in `config/edm-rules.yaml`.
- **D3** Closed lists are `enum` lists on the owning attribute; ISO code lists are format rules; the EDM stores no reference data.
- **D11** Every taxonomy is data in one generic model: `taxonomy`, `taxonomy_version`, `taxonomy_node`, `taxonomy_closure`, `transaction_hierarchy`.
- **D12** Until Studio verification is done, model files come from the one-time builder in `migration/` and are marked `edmBuiltBy`.

All decisions: [docs/decisions/](docs/decisions/README.md). Principles:
[docs/architecture/principles.md](docs/architecture/principles.md).

## Spec workflow

Draft → Approved → Implemented → Verified ([specs/README.md](specs/README.md)).
Do not start implementation before a spec is Approved. If the work needs
something the spec does not cover, stop and update the spec. When a
requirement is unclear, ask; do not guess.

## Before you propose a change

```bash
make test     # tests for the checks and CI helpers
make check    # every governance check on the model files
```

Both must pass. With Hackolade installed, also `make hk-stale` and
`make hk-validate`. When a check fails, read its message (file, object, rule)
and the rule in `config/edm-rules.yaml`; fix the model in Studio, not the rule.

## Where things are

| Need | Look in |
| --- | --- |
| Rules the checks apply | `config/edm-rules.yaml` |
| The checks | `tools/` (`make check-<name>`) |
| Custom properties, naming, glossary for Studio | `hackolade/` (`make hackolade-config`) |
| How to build an application model | `docs/workflows/greenfield.md`, `docs/workflows/brownfield.md` |
| Hackolade CLI in CI | `ci/`, `.github/workflows/` |
| What is not migrated yet | `docs/migration-backlog.md` |
