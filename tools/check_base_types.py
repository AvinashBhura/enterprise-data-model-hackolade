"""Entities carry the attributes of every base type in edmComposes, exactly as the contract says (D2).

Usage: python3 tools/check_base_types.py [--repo PATH] [--rules PATH]
"""

import sys

from edm.cli import run

if __name__ == "__main__":
    sys.exit(run(["base_types"]))
