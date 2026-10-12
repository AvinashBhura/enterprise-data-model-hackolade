.PHONY: help install check test hackolade-config clean check-layers check-cycles check-naming check-metadata check-foundation-kind check-base-types check-enums check-junctions check-references check-deviations check-format check-ownership check-foundation-contract hk-stale hk-validate hk-diff hk-release

PYTHON ?= python3

help:
	@echo "Enterprise Data Model — common commands"
	@echo ""
	@echo "  make install                  Install the checks' only dependency (PyYAML)"
	@echo "  make check                    Run every governance check"
	@echo "  make check-<name>             Run one check: layers, cycles, naming, metadata, foundation-kind, base-types, enums, junctions, references, deviations, format, ownership, foundation-contract"
	@echo "  make test                     Test the checks"
	@echo "  make hackolade-config         Show which Hackolade settings would be installed (dry run)"
	@echo "  make hackolade-config FORCE=1 Install them into ~/.hackolade/options, after a backup"
	@echo "  make hk-stale                 Hackolade CLI: are models behind their parents? (needs a licence)"
	@echo "  make hk-validate              Hackolade CLI: forward-engineer physical models with validation"
	@echo "  make hk-diff [BASE=origin/main]  Hackolade CLI: what changed against BASE"
	@echo "  make hk-release TAG=vX.Y.Z    Hackolade CLI: DDL, JSON Schema, docs and manifest into build/release"
	@echo "  make clean                    Remove caches and build output"
	@echo ""
	@echo "Run 'make check' and 'make test' before every pull request."

install:
	$(PYTHON) -m pip install -e .

check:
	@$(PYTHON) tools/run_checks.py

check-layers:
	@$(PYTHON) tools/check_layers.py

check-cycles:
	@$(PYTHON) tools/check_cycles.py

check-naming:
	@$(PYTHON) tools/check_naming.py

check-metadata:
	@$(PYTHON) tools/check_metadata.py

check-foundation-kind:
	@$(PYTHON) tools/check_foundation_kind.py

check-base-types:
	@$(PYTHON) tools/check_base_types.py

check-enums:
	@$(PYTHON) tools/check_enums.py

check-junctions:
	@$(PYTHON) tools/check_junctions.py

check-references:
	@$(PYTHON) tools/check_references.py

check-deviations:
	@$(PYTHON) tools/check_deviations.py

check-format:
	@$(PYTHON) tools/check_format.py

check-ownership:
	@$(PYTHON) tools/check_ownership.py

check-foundation-contract:
	@$(PYTHON) tools/check_foundation_contract.py

test:
	@$(PYTHON) -m unittest discover -s tests

hackolade-config:
	@$(PYTHON) tools/install_hackolade_config.py $(if $(FORCE),--force,)

# Hackolade CLI steps (ci/hk.sh). HK is the CLI command: `hackolade` when Studio
# is installed, or HK="docker compose -f ci/compose.yml run --rm hck".
HK ?= hackolade
BASE ?= origin/main

hk-stale:
	@HK="$(HK)" PYTHON=$(PYTHON) ci/hk.sh stale

hk-validate:
	@HK="$(HK)" PYTHON=$(PYTHON) ci/hk.sh validate

hk-diff:
	@HK="$(HK)" PYTHON=$(PYTHON) ci/hk.sh diff $(BASE)

hk-release:
	@test -n "$(TAG)" || (echo "usage: make hk-release TAG=vX.Y.Z" && exit 2)
	@HK="$(HK)" PYTHON=$(PYTHON) ci/hk.sh release $(TAG)

clean:
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
	rm -rf build/ *.egg-info
