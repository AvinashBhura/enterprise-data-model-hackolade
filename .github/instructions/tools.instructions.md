---
applyTo: "tools/**"
---

# Governance checks

- Checks read `.hck.json` files and `config/edm-rules.yaml`; they never write
  model files.
- Python 3.10+, standard library plus PyYAML only. Tests use `unittest`.
- Every configurable rule lives in `config/edm-rules.yaml`, not in code.
- Each check has its own command `tools/check_<name>.py` and Make target
  `check-<name>`, exits non-zero on a violation, and names the file, object and
  rule in each message.
- Every check has at least one passing and one failing test in
  `tests/test_checks.py`. Run `make test` and `make check`.
