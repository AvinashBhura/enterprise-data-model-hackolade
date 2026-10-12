"""The same attribute name carries the same enum values everywhere, unless listed as an intended difference (D3).

Usage: python3 tools/check_enums.py [--repo PATH] [--rules PATH]
"""

import sys

from edm.cli import run

if __name__ == "__main__":
    sys.exit(run(["enums"]))
