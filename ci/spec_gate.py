"""Spec gate (spec 0006, requirement 1).

A pull request that changes src/, tools/, config/ or hackolade/ must name a spec
in its title as [NNNN], and that spec must be Approved (or Implemented or
Verified) on the base branch.

Usage (in CI):
    python ci/spec_gate.py --title "$PR_TITLE" --base origin/main
Changed files are read from `git diff --name-only BASE...HEAD` unless given
with --changed.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys

GUARDED = ("src/", "tools/", "config/", "hackolade/")
ACCEPTED = ("Approved", "Implemented", "Verified")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def spec_status(base: str, number: str) -> str | None:
    """The Status line of specs/NNNN-*/spec.md on the base branch, or None."""
    listing = git("ls-tree", "-r", "--name-only", base, "specs/")
    paths = [p for p in listing.splitlines() if re.fullmatch(rf"specs/{number}-[^/]+/spec\.md", p)]
    if not paths:
        return None
    text = git("show", f"{base}:{paths[0]}")
    m = re.search(r"^Status:\s*(.+)$", text, re.M)
    return m.group(1).strip() if m else ""


def gate(title: str, changed: list[str], status_of) -> tuple[bool, str]:
    guarded = [f for f in changed if f.startswith(GUARDED)]
    if not guarded:
        return True, "no governed path changed; no spec needed"
    numbers = re.findall(r"\[(\d{4})\]", title)
    if not numbers:
        return False, (f"this pull request changes {', '.join(sorted({f.split('/')[0] for f in guarded}))}; "
                       "name its spec in the title, for example '[0003] Talent Acquisition model'")
    for n in numbers:
        status = status_of(n)
        if status and status.startswith(ACCEPTED):
            return True, f"spec {n} is '{status}' on the base branch"
    return False, f"spec(s) {', '.join(numbers)} not found or not Approved on the base branch"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--title", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--changed", nargs="*")
    args = ap.parse_args(argv)
    changed = args.changed if args.changed is not None else git("diff", "--name-only", f"{args.base}...HEAD").split()
    ok, message = gate(args.title, changed, lambda n: spec_status(args.base, n))
    print(("spec gate: ok — " if ok else "spec gate: FAIL — ") + message)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
