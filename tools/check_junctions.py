"""A Bridge/Junction entity has its own key and exactly two relationships.

Usage: python3 tools/check_junctions.py [--repo PATH] [--rules PATH]
"""

import sys

from edm.cli import run

if __name__ == "__main__":
    sys.exit(run(["junctions"]))
