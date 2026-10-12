"""Required custom properties are present and hold allowed values.

Usage: python3 tools/check_metadata.py [--repo PATH] [--rules PATH]
"""

import sys

from edm.cli import run

if __name__ == "__main__":
    sys.exit(run(["metadata"]))
