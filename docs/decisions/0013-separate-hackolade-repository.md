# D13 — The Hackolade EDM lives in its own repository

Status: Accepted
Date: 2026-10-12
Approved by: Avinash Bhura (instruction of 2026-10-12)

## Context

The move to Hackolade was built on branch `migration/hackolade` of the LinkML
repository, `AvinashBhura/enterprise-data-model`. The owner wants the Hackolade
EDM in a separate repository.

## Decision

- The Hackolade EDM lives in `AvinashBhura/enterprise-data-model-hackolade`. Its
  history starts with the state that specs 0001–0006 produced; the LinkML
  history is not copied.
- The LinkML repository stays as it is: its `main` branch and the tag
  `linkml-final-v0.5.0` are the archive of the LinkML EDM and
  the source the one-time builder reads (D5, D10).
- The builder (`migration/build.py`, `migration/compare.py`) finds the tag in a
  clone of the LinkML repository next to this one, in `EDM_LINKML_REPO`, or
  through `--linkml-repo` or `--linkml-src`.

## Consequences

- This repository holds no LinkML file. Frozen domains, retired processes and
  sample applications are recovered from the LinkML repository
  (`docs/migration-backlog.md`).
- The tag `linkml-final-v0.5.0` is kept in the local clone of the LinkML
  repository and is not pushed to GitHub (owner's choice, 2026-10-12). The
  builder runs only where that clone exists; the frozen content stays on
  GitHub on the LinkML repository's `main` branch.
- The branch `migration/hackolade` in the LinkML repository is no longer needed
  once this repository holds the work; delete it or keep it as a record.
