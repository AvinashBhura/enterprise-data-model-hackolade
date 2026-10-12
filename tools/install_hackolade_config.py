"""Install the repository's Hackolade settings into this user's Hackolade options folder.

Hackolade Studio reads custom properties and naming settings per user, from
~/.hackolade/options, not from the repository. This copies the versioned
settings from hackolade/ into place.

Dry run by default: lists what would change. Apply with --force (make
hackolade-config FORCE=1); existing files are backed up first.

Usage:  python3 tools/install_hackolade_config.py [--force] [--options PATH]
"""

from __future__ import annotations

import argparse
import filecmp
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "hackolade"

# (source folder in the repo, destination relative to the options folder)
MAPPINGS = [
    ("customProperties/Polyglot", "Polyglot/customProperties"),
    ("customProperties/PostgreSQL", "PostgreSQL/customProperties"),
    ("naming", "naming"),
]

NAMING_SETTINGS = """\
Naming conventions (set once in Studio: Tools > Options > Naming Conventions).
Hackolade does not document the file these settings are stored in, so set them by hand:

  For targets Polyglot and PostgreSQL:
    Enable name coupling ........ Business-to-Technical
    Conversion file ............. {abbreviations}
    Invalid characters .......... !?.,:;()=+-*@/\\   replaced by  _
    Case conversion ............. snake_case
    Display ..................... Business name

These match config/edm-rules.yaml (naming.technical_name).
"""


def plan(options: Path) -> list[tuple[str, Path, Path]]:
    """(status, source, destination) for every file; status is new, changed or same."""
    items = []
    for src_rel, dst_rel in MAPPINGS:
        src_root = SOURCE / src_rel
        for src in sorted(p for p in src_root.rglob("*") if p.is_file() and p.name != "README.md"):
            dst = options / dst_rel / src.relative_to(src_root)
            if not dst.exists():
                status = "new"
            elif filecmp.cmp(src, dst, shallow=False):
                status = "same"
            else:
                status = "changed"
            items.append((status, src, dst))
    return items


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--force", action="store_true", help="apply the changes (after a backup)")
    parser.add_argument("--options", type=Path,
                        default=Path(os.environ.get("HACKOLADE_OPTIONS", Path.home() / ".hackolade" / "options")),
                        help="Hackolade options folder (default: ~/.hackolade/options or $HACKOLADE_OPTIONS)")
    args = parser.parse_args(argv)
    options = args.options.expanduser()

    items = plan(options)
    for status, src, dst in items:
        print(f"  {status:8} {dst}")
    to_change = [i for i in items if i[0] != "same"]
    print(f"{len(to_change)} file(s) to add or change in {options}")

    if not args.force:
        if to_change:
            print("Dry run: nothing written. Apply with: make hackolade-config FORCE=1")
    else:
        existing = [i for i in to_change if i[0] == "changed"]
        if existing:
            backup = options / f"edm-backup-{datetime.now():%Y%m%d-%H%M%S}"
            for _, _, dst in existing:
                target = backup / dst.relative_to(options)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(dst, target)
            print(f"Backed up {len(existing)} file(s) to {backup}")
        for _, src, dst in to_change:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        print(f"Applied {len(to_change)} file(s). Restart Hackolade Studio to load them.")

    print()
    print(NAMING_SETTINGS.format(abbreviations=options / "naming" / "abbreviations.csv"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
