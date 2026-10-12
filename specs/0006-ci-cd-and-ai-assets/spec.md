# 0006 — CI/CD pipeline and AI development assets

Status: Implemented (2026-10-12); Hackolade stages awaiting a concurrent licence
Owner: EDM architecture
Decisions: [D4](../../docs/decisions/0004-generation-by-hackolade.md), [D9](../../docs/decisions/0009-licences-and-version.md)
Depends on: 0001 Verified. The Hackolade stages also need spike T5 passed and a concurrent licence.

## Problem

The current pipeline runs LinkML validation. The current agent assets (8 Claude
agents, 4 skills, a 283-line `CLAUDE.md`) assume LinkML and serve only Claude.
The repository needs a pipeline built on the Python checks and the Hackolade CLI,
and one set of instructions that Claude, GitHub Copilot and Codex all follow.

## Scope

In scope:
- GitHub Actions workflows, the Hackolade CLI Docker image, Makefile targets they call.
- `AGENTS.md`, `CLAUDE.md`, Copilot instructions and prompts, Claude agents and skills, agent memory folders.

Out of scope:
- Pipelines in application repositories (they follow `docs/workflows/greenfield.md`).
- Publishing to a data catalogue.

## Requirements

### Pipeline

1. `governance.yml` runs on every pull request and push to `main`, with no Hackolade licence:
   - `make test` and `make check`;
   - the spec gate: a pull request that changes `src/`, `tools/`, `config/` or `hackolade/` must name an Approved spec in its title (`[NNNN]`), and that spec must have `Status: Approved` or later on the base branch.
2. `hackolade.yml` runs on every pull request that changes `src/`, inside the image from `ci/Dockerfile`:
   - **stale gate**: on a scratch copy, run `extRefUpdate` and `polyglotUpdate` for each changed model, then `compMod` against the committed file. Any difference fails the build: an upstream change was not pulled in;
   - **schema gate**: `forwEng --validateSchema=true` for every physical model;
   - **change report**: `compMod` of each changed model against the base branch, posted as a pull request comment.
3. `release.yml` runs on tags `v*`: generates DDL, JSON Schema and Markdown docs for every model with `forwEng` and `genDoc`, and attaches them to the GitHub release with the tag, Studio version and plugin versions in a manifest file.
4. A DDL smoke test runs the generated PostgreSQL DDL against a PostgreSQL 16 service container in `hackolade.yml`.
5. Generated files are never committed to this repository (D4).
6. If the `HACKOLADE_LICENSE` secret is missing, `hackolade.yml` reports "skipped: no licence" and does not fail. Modellers then run the same steps locally with `make hk-stale`, `make hk-validate`, `make hk-diff`.

### Docker image

7. `ci/Dockerfile` builds from the official `hackolade/studio` image at a pinned version (D9), with the plugins listed in `ci/plugins.txt` (at least PostgreSQL) at pinned versions, and the repository's custom property and naming settings copied in.
8. The licence key comes only from the `HACKOLADE_LICENSE` secret. It is never written to a file in the repository or a log.

### AI assets

9. `AGENTS.md` is the one canonical instruction file. It states: the layers and dependency rule; the Strict-Foundation rule; single ownership; D2, D3 and D11 in one line each; the spec workflow; "never hand-edit `.hck.json`"; which `make` targets to run before proposing a change.
10. `CLAUDE.md` imports `AGENTS.md` (`@AGENTS.md`) and adds only Claude-specific notes. `.github/copilot-instructions.md` tells Copilot to follow `AGENTS.md` and repeats its five hard rules. Codex reads `AGENTS.md` directly.
11. Path-specific Copilot instructions in `.github/instructions/`: one for `src/**`, one for `tools/**`, one for `specs/**`.
12. Claude agents in `.claude/agents/`, replacing the eight LinkML-era agents:

    | Agent | Job | Replaces |
    | --- | --- | --- |
    | `spec-author` | Turns a request into a spec draft from the template; never writes implementation | new |
    | `model-reviewer` | Reviews a model change against the principles and decisions, reading the `compMod` report and the check output | edm-semantic-architect, enterprise-architecture-board, semantic-reuse-analyzer, stewardship-intelligence |
    | `governance-checker` | Runs `make check`, explains each failure and the fix | layer-boundary-governor, process-separation-auditor |
    | `application-modeller` | Guides greenfield derivation and brownfield gap analysis | vendor-projection-auditor, enterprise-linkml-modeler |

13. The 27 principles encoded in the old agents move to `docs/architecture/principles.md` (merged with what is there), so they survive the rewrite. Agents refer to that file instead of repeating it.
14. Claude skills in `.claude/skills/<name>/SKILL.md`, each with name and description front matter: `hackolade-cli` (the commands this repository uses and their arguments), `edm-modelling-rules`, `spec-workflow`.
15. Copilot prompt files in `.github/prompts/`: `new-spec.prompt.md`, `review-model-change.prompt.md`, `explain-check-failure.prompt.md`.
16. `.claude/agent-memory/<agent>/` exists for each new agent, with a README saying what may be kept there (learned conventions, recurring review findings) and what may not (secrets, personal data, anything that belongs in a decision record).
17. No AI asset mentions LinkML, except `docs/migration-backlog.md` and the decision records.

## Acceptance criteria

1. A test pull request that changes `src/` without naming a spec fails the spec gate. A test pull request naming an Approved spec passes it.
2. With a licence: a test pull request that edits a Common definition without refreshing a dependent model fails the stale gate.
3. Without a licence: `hackolade.yml` is skipped and reported, and `governance.yml` still runs.
4. A test tag produces a release with DDL, JSON Schema, docs and a manifest.
5. `grep -ri linkml AGENTS.md CLAUDE.md .github .claude` returns nothing.
6. Each skill has valid front matter. Checked by a test.

## Validation

Run the four test pull requests and the test tag in a fork or a scratch branch. Record each run's link in the spec's pull request.

## Resolved questions

Approved by Avinash Bhura on 2026-10-12 with the recommended answers.

1. Every third-party GitHub Action is pinned to a full commit hash, with the version tag in a comment. Dependabot proposes updates.

## Amendments — 2026-10-12

1. **Docker image (req 7).** Hackolade now publishes a ready-made CLI image, `hackolade/hck-cli`, with every plugin bundled at versions fixed by its tag. `ci/Dockerfile` builds on it at a pinned tag (8.13.0 or later) and adds the repository's custom properties and naming files. `ci/plugins.txt` lists the plugins needed with minimum versions; `ci/check_plugins.py` checks them against the image's `version` output on every run.
2. **Steps.** The Hackolade steps are in `ci/hk.sh` (`stale`, `validate`, `diff`, `release`), called by the workflows and by `make hk-stale`, `hk-validate`, `hk-diff`, `hk-release`. The spec gate is `ci/spec_gate.py`. Both have tests in `tests/test_ci.py`.
3. **Interim workflow.** `governance.yml` replaces `validate.yml`, which is deleted.
4. **Acceptance criteria 1–4** need test pull requests and a tag on GitHub (and a concurrent licence for 2 and 4); recorded when run. Criteria 5 and 6 are checked by `tests/test_repo.py`.
