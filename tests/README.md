# tests

Tests for the checks in `tools/`, using the standard `unittest` module. Run with `make test`.

- `test_checks.py` — one passing and at least one failing case per check, on small model files built in a temporary folder by `support.py`.
- `test_report_gaps.py` — the brownfield gap report on fixture models.
- `test_repo.py` — repository rules: folder READMEs, the glossary CSV matches the glossary page, the rules file is complete, the real repository passes `make check`, `make hackolade-config` behaves as specified, every model file's internal references resolve, and the AI assets are valid (skill front matter, no old schema-language terms).

The fixture files carry only the keys the checks read. They are not meant to open in Hackolade Studio.
