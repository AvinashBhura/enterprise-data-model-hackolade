"""Model files use a supported persistence schema version and a recent enough Studio version.

Usage: python3 tools/check_format.py [--repo PATH] [--rules PATH]
"""

import sys

from edm.cli import run

if __name__ == "__main__":
    sys.exit(run(["format"]))
