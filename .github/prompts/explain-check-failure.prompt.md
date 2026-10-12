---
mode: agent
description: Explain a failing governance check and how to fix it
---

Run `make check` (or the single check named below) and, for each violation:

1. Quote the message: file, object, rule.
2. Explain the rule in one or two sentences, citing its section in
   `config/edm-rules.yaml` and the decision or principle behind it.
3. Give the fix as steps in Hackolade Studio (or in the rules file, if the rule
   itself should change, which needs a spec).

Check: ${input:check:Name of the check, or leave empty for all}
