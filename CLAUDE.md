@AGENTS.md

## Claude-specific notes

- Agents in `.claude/agents/`: `spec-author` (drafts specs), `model-reviewer`
  (reviews model changes), `governance-checker` (runs and explains
  `make check`), `application-modeller` (greenfield and brownfield application
  models). Use them for those jobs instead of working from scratch.
- Skills in `.claude/skills/`: `hackolade-cli`, `edm-modelling-rules`,
  `spec-workflow`.
- Each agent may keep notes in `.claude/agent-memory/<agent>/`; read its README
  for what may and may not be kept there.
- You cannot open Hackolade Studio. When a change needs a model edit, write the
  exact steps for the modeller (entity, attribute, property, value) instead of
  editing the `.hck.json` file.
