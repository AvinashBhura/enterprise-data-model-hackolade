"""No cycle in the dependency graph between model files, transitive included.

Usage: python3 tools/check_cycles.py [--repo PATH] [--rules PATH]
"""

import sys

from edm.cli import run

if __name__ == "__main__":
    sys.exit(run(["cycles"]))
