"""Run every EDM check, or the ones named. Exit code 1 if any check fails.

Usage:  python3 tools/run_checks.py                      # all checks
        python3 tools/run_checks.py layers cycles        # selected checks
        python3 tools/run_checks.py --repo PATH [--rules PATH] [checks...]
"""

import sys

from edm.checks import CHECKS
from edm.cli import run


def split_args(argv):
    names, options, i = [], [], 0
    while i < len(argv):
        arg = argv[i]
        if arg in ("--repo", "--rules") and i + 1 < len(argv):
            options += [arg, argv[i + 1]]
            i += 2
        elif arg.startswith("-"):
            options.append(arg)
            i += 1
        else:
            names.append(arg)
            i += 1
    return names, options


if __name__ == "__main__":
    names, options = split_args(sys.argv[1:])
    names = names or list(CHECKS)
    unknown = [n for n in names if n not in CHECKS]
    if unknown:
        sys.exit(f"unknown check(s): {', '.join(unknown)}; choose from {', '.join(CHECKS)}")
    sys.exit(run(names, options))
