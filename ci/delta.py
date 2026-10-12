"""Read a compMod delta model (ci/hk.sh).

--empty FILE    exit 0 if the delta model holds no change, 1 otherwise
--summary FILE  print a Markdown summary of the entities and relationships in it

compMod writes the differences as a Hackolade model; an empty comparison has
no entities and no relationships. To verify on first CI run with a licence
(docs/workflows/studio-verification.md).
"""

import argparse
import json
import sys
from pathlib import Path


def changes(delta: dict) -> tuple[list[str], list[str]]:
    entities = sorted(c.get("collectionName") or c.get("name") or "?" for c in delta.get("collections", []))
    relationships = sorted(r.get("name") or "?" for r in delta.get("relationships", []))
    return entities, relationships


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--empty", type=Path)
    ap.add_argument("--summary", type=Path)
    ap.add_argument("--title", default="")
    args = ap.parse_args(argv)
    path = args.empty or args.summary
    delta = json.loads(path.read_text(encoding="utf-8")) if path and path.exists() else {}
    entities, relationships = changes(delta)
    if args.empty:
        return 0 if not (entities or relationships) else 1
    print(f"\n### {args.title or path.name}\n")
    if not (entities or relationships):
        print("No change.")
    for e in entities:
        print(f"- entity `{e}`")
    for r in relationships:
        print(f"- relationship `{r}`")
    return 0


if __name__ == "__main__":
    sys.exit(main())
