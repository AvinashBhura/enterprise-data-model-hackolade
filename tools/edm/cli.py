"""Command-line runner shared by every tools/check_*.py script and tools/run_checks.py."""

from __future__ import annotations

import argparse
from pathlib import Path

from .checks import CHECKS, Context
from .model import load_models
from .report import print_report
from .rules import Rules

REPO = Path(__file__).resolve().parents[2]


def run(names: list[str], argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="EDM governance checks: " + ", ".join(names))
    parser.add_argument("--repo", type=Path, default=REPO, help="repository root (default: this repository)")
    parser.add_argument("--rules", type=Path, default=None, help="rules file (default: <repo>/config/edm-rules.yaml)")
    args = parser.parse_args(argv)
    repo = args.repo.resolve()
    rules = Rules.load(repo, args.rules)
    models = load_models(repo, rules)
    ctx = Context(repo, rules, models)
    code = 0
    for name in names:
        code |= print_report(name, CHECKS[name](ctx), len(models))
    return code
