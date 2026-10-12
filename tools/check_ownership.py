"""Each entity is defined in exactly one model.

Usage: python3 tools/check_ownership.py [--repo PATH] [--rules PATH]
"""

import sys

from edm.cli import run

if __name__ == "__main__":
    sys.exit(run(["ownership"]))
