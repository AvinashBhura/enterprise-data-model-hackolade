"""Every entity carries the attributes of its Foundation kind, as the Foundation model defines them (D12).

Usage: python3 tools/check_foundation_contract.py [--repo PATH] [--rules PATH]
"""

import sys

from edm.cli import run

if __name__ == "__main__":
    sys.exit(run(["foundation_contract"]))
