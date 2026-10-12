"""Polymorphic reference pairs name entity types that exist in the EDM.

Usage: python3 tools/check_references.py [--repo PATH] [--rules PATH]
"""

import sys

from edm.cli import run

if __name__ == "__main__":
    sys.exit(run(["references"]))
