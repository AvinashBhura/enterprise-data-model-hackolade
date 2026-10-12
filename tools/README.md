# tools — governance checks

Python checks that read Hackolade model files and `config/edm-rules.yaml`. They never write model files. Python 3.10+ and PyYAML only.

| Command | Make target | Rule |
| --- | --- | --- |
| `check_layers.py` | `check-layers` | A model depends only on models in its own or a lower layer |
| `check_cycles.py` | `check-cycles` | No dependency cycle between model files |
| `check_naming.py` | `check-naming` | Business and technical names follow the naming rules |
| `check_metadata.py` | `check-metadata` | Required custom properties are present and valid |
| `check_foundation_kind.py` | `check-foundation-kind` | Domain, Process and Application entities specialise one Foundation kind |
| `check_base_types.py` | `check-base-types` | Entities match the base-type contracts they list in `edmComposes` |
| `check_enums.py` | `check-enums` | The same attribute name carries the same enum values everywhere |
| `check_junctions.py` | `check-junctions` | Junction entities name the two entities they connect (`edmConnects`), relate to both, and have their own key |
| `check_references.py` | `check-references` | Polymorphic reference pairs are configured and name real entities |
| `check_deviations.py` | `check-deviations` | No local change to derived Foundation/Common entities; others have a reason |
| `check_format.py` | `check-format` | Supported persistence schema and Studio version |
| `check_ownership.py` | `check-ownership` | Each entity is defined in one model only |
| `check_foundation_contract.py` | `check-foundation-contract` | Every entity carries its Foundation kind's attributes as the Foundation model defines them (D12) |

`run_checks.py` runs all of them (`make check`). Every command accepts `--repo` and `--rules`, and exits non-zero on any violation. Output names the file, object and rule.

`report_gaps.py` writes the brownfield gap report: an application model against the Domain ([docs/workflows/brownfield.md](../docs/workflows/brownfield.md)).

`install_hackolade_config.py` installs the settings in `hackolade/` into your Hackolade options folder (`make hackolade-config`).

The shared code is in `edm/`: `model.py` reads model files, `rules.py` reads the rules, `checks.py` holds the checks.
