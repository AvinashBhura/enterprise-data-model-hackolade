# Specs — spec-driven development

Every change to this repository starts as a spec. No model, check, config or
pipeline change is merged without an **Approved** spec that covers it.

## Workflow

| Status | Meaning | Who moves it |
| --- | --- | --- |
| Draft | Written, open for review | Author |
| Approved | Requirements and acceptance criteria agreed | EDM architecture owner |
| Implemented | Work done on a branch, all acceptance checks pass locally | Author |
| Verified | Merged to `main`, CI green, acceptance criteria re-checked | Reviewer |

1. Create `specs/NNNN-short-name/spec.md` from the template below. Use the next free number.
2. Open a pull request with only the spec. Discuss and change it there.
3. When approved, set `Status: Approved` and merge.
4. Implement on a new branch. Add `tasks.md` if the work has more than a few steps.
5. Every implementation pull request names its spec in the title, for example `[0003] Talent Acquisition model`.
6. If the work needs something the spec does not cover, stop. Update the spec and get it approved again.

CI fails a pull request that changes `src/`, `tools/`, `config/` or `hackolade/`
without naming an Approved spec.

## Rules for AI agents

- Do not start implementation without an Approved spec.
- Do not hand-edit `.hck.json` files. Model changes are made in Hackolade Studio
  or with the Hackolade CLI. The file format is not a published contract.
- When a spec is unclear, ask. Do not guess.

## Template

```markdown
# NNNN — Title

Status: Draft
Owner: <name>
Decisions: <links to docs/decisions records this spec depends on>
Depends on: <other specs>

## Problem
What is wrong or missing, in two or three sentences.

## Scope
In scope / out of scope, as two short lists.

## Requirements
Numbered. Each one testable.

## Acceptance criteria
Numbered. Each one says how it is checked (command, review step, or Studio action).

## Validation
The commands and manual checks that prove the acceptance criteria.

## Open questions
Anything that needs a decision before or during the work.
```

## Index

| Spec | Title | Status |
| --- | --- | --- |
| [0001](0001-repository-and-governance-checks/spec.md) | Repository structure and governance checks | Implemented (amended for D12) |
| [0002](0002-foundation-and-common/spec.md) | Foundation and Common models | Implemented, awaiting Studio verification |
| [0003](0003-hr-and-talent-acquisition/spec.md) | HR domain and Talent Acquisition | Implemented, awaiting Studio verification |
| [0004](0004-core-process-model/spec.md) | Core process model | Implemented, awaiting Studio verification |
| [0005](0005-candidate-journey/spec.md) | Candidate Journey physical model | Implemented, awaiting Studio verification |
| [0006](0006-ci-cd-and-ai-assets/spec.md) | CI/CD pipeline and AI development assets | Implemented; Hackolade stages need a licence |

"Awaiting Studio verification": the model files were written by `migration/build.py` without a Hackolade licence ([D12](../docs/decisions/0012-complete-without-studio.md)). [docs/workflows/studio-verification.md](../docs/workflows/studio-verification.md) lists what to do in Studio before each spec can be Verified.
