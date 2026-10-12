# Copilot instructions

Follow [AGENTS.md](../AGENTS.md) at the repository root. It is the one source of
instructions for this repository.

The five hard rules, repeated here:

1. Every Domain, Process and Application entity specialises exactly one
   Foundation kind and carries that kind's attributes.
2. Each entity is defined in one model; others derive or reference it.
3. Workflow state lives in the Process layer, never on Domain entities.
4. Never hand-edit `.hck.json` files; models change in Hackolade Studio or the CLI.
5. No change to `src/`, `tools/`, `config/` or `hackolade/` without an Approved
   spec named as `[NNNN]` in the pull request title.

Run `make test` and `make check` before proposing a change.
