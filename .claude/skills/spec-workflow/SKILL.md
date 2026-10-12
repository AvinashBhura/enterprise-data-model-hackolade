---
name: spec-workflow
description: How work moves through specs in this repository - statuses, who moves them, the template, and the spec gate in CI. Use before starting any change to src/, tools/, config/ or hackolade/.
---

# Spec workflow

Every change to `src/`, `tools/`, `config/` or `hackolade/` needs an Approved spec.

| Status | Meaning | Who sets it |
| --- | --- | --- |
| Draft | Written, open for review | Author |
| Approved | Requirements and acceptance criteria agreed | EDM architecture owner |
| Implemented | Done on a branch; acceptance checks pass locally | Author |
| Verified | Merged; CI green; acceptance criteria re-checked | Reviewer |

## Steps

1. Copy the template in `specs/README.md` to `specs/NNNN-short-name/spec.md` (next free number). Status: Draft.
2. Open a pull request with only the spec. Change it until approved.
3. Implement on a branch. Add `tasks.md` for work with more than a few steps.
4. Name the spec in the pull request title: `[0003] Talent Acquisition model`. CI's spec gate (`ci/spec_gate.py`) fails the pull request otherwise, or if the spec is not Approved on the base branch.
5. Set Implemented when the acceptance criteria pass; the reviewer sets Verified after merge.

## Rules

- Requirements are numbered and testable; acceptance criteria name the command or Studio action that checks them.
- A design choice that changes the architecture needs a decision record in `docs/decisions/` first.
- If the work needs something the spec does not cover, stop and update the spec.
- Ask when a requirement is unclear; do not guess.
