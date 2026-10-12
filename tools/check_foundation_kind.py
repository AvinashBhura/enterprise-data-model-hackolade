"""Every Domain, Process and Application entity specialises exactly one Foundation kind.

Usage: python3 tools/check_foundation_kind.py [--repo PATH] [--rules PATH]
"""

import sys

from edm.cli import run

if __name__ == "__main__":
    sys.exit(run(["foundation_kind"]))
