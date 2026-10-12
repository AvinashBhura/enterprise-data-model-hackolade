---
mode: agent
description: Draft a new spec from a change request
---

Draft a spec for the change described below, following `specs/README.md` and
`AGENTS.md`.

1. Read `specs/README.md`, the related decisions in `docs/decisions/`, and the
   README of every model folder the change touches.
2. Pick the next free number. Create `specs/NNNN-short-name/spec.md` from the
   template, with `Status: Draft`.
3. Write testable requirements and acceptance criteria that name the command or
   Studio action that checks each one.
4. List every open question instead of guessing. Do not write implementation.
5. Add the spec to the index in `specs/README.md`.

Change request: ${input:request:Describe the change}
