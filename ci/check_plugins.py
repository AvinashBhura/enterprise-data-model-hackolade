"""Check that the CLI image has the plugins in ci/plugins.txt at their minimum versions.

Usage: hck-cli version | python ci/check_plugins.py ci/plugins.txt
The `version` command lists "<Plugin>: <version>, commit: ..., built: ..." lines.
"""

import re
import sys


def parse_version(v: str) -> tuple:
    return tuple(int(x) for x in re.findall(r"\d+", v)[:3])


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    wanted = {}
    with open(argv[0], encoding="utf-8") as fh:
        for line in fh:
            line = line.split("#", 1)[0].strip()
            if line:
                name, minimum = line.rsplit(None, 1)
                wanted[name] = minimum
    text = sys.stdin.read()
    found = dict(re.findall(r"^\s*([A-Za-z0-9 _.-]+?):\s*(\d+\.\d+\.\d+)", text, re.M))
    bad = 0
    for name, minimum in wanted.items():
        have = found.get(name)
        if have is None:
            print(f"missing plugin: {name}")
            bad = 1
        elif parse_version(have) < parse_version(minimum):
            print(f"plugin {name} {have} is older than {minimum}")
            bad = 1
        else:
            print(f"plugin {name} {have} ok")
    return bad


if __name__ == "__main__":
    sys.exit(main())
