"""Business and technical names follow the rules in config/edm-rules.yaml.

Usage: python3 tools/check_naming.py [--repo PATH] [--rules PATH]
"""

import sys

from edm.cli import run

if __name__ == "__main__":
    sys.exit(run(["naming"]))
