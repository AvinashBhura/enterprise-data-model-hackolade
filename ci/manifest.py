"""Write the release manifest (spec 0006, requirement 3): tag, Studio and plugin versions, models."""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--version-file", type=Path, required=True, help="output of the CLI `version` command")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    text = args.version_file.read_text(encoding="utf-8", errors="ignore") if args.version_file.exists() else ""
    studio = re.search(r"Hackolade version:\s*(\S+)", text)
    plugins = dict(re.findall(r"^\s*([A-Za-z0-9 _.-]+?):\s*(\d+\.\d+\.\d+)", text, re.M))
    plugins.pop("Hackolade version", None)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    models = {}
    for p in sorted(Path("src").rglob("*.hck.json")):
        models[p.as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    manifest = {"tag": args.tag, "commit": commit, "studio_version": studio.group(1) if studio else None,
                "plugins": plugins, "models": models}
    args.out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"manifest: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
