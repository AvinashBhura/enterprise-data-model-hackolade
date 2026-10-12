---
mode: agent
description: Review a model change against the EDM rules
---

Review the model change in this pull request.

1. Run `make check` and read the `compMod` change report (CI comment or
   `make hk-diff`).
2. Check the change against `AGENTS.md`, `docs/architecture/principles.md` and
   the decisions in `docs/decisions/`: layer placement, Foundation kind, single
   owner, workflow state, enums, polymorphic references, deviations in derived
   models.
3. Check that the spec named in the title covers every change, and that the
   model folder's README is updated.
4. Report: verdict (approve / changes needed), each finding with file, entity
   and the rule it breaks, and the fix a modeller makes in Studio.
