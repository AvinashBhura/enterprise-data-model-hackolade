"""A model depends only on models in its own or a lower layer.

Usage: python3 tools/check_layers.py [--repo PATH] [--rules PATH]
"""

import sys

from edm.cli import run

if __name__ == "__main__":
    sys.exit(run(["layers"]))
