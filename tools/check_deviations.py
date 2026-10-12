"""No local change to derived Foundation/Common entities; other deviations carry a reason.

Usage: python3 tools/check_deviations.py [--repo PATH] [--rules PATH]
"""

import sys

from edm.cli import run

if __name__ == "__main__":
    sys.exit(run(["deviations"]))
