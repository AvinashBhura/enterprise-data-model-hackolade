"""Check builder-written model files against files saved by Hackolade Studio (D12).

Two kinds of check, before the files are opened in Studio:

1. Integrity: every GUID is unique; every reference inside a file resolves
   (relationship ends, foreign-key fields, buckets, keys, indexes, external and
   polyglot definitions); every linked model file exists and holds the entity
   the link names, with the GUID a polyglot copy claims.
2. Shape: every key the builder writes on a model, container, entity, attribute,
   relationship or definition is a key Studio itself writes on that kind of
   object in Hackolade's public sample models, or an EDM custom property.

Usage:
    python migration/validate_structure.py --samples PATH/TO/demo-models-read-only [files...]

Without files, checks every .hck.json under src/. Exits non-zero on any problem.
The samples are https://github.com/hackolade/demo-models-read-only (cloned locally).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CUSTOM = {
    "model": {"edmLayer", "edmDomain", "edmSubdomain", "edmBuiltBy"},
    "collection": {"layer", "foundationKind", "entityType", "steward", "edmComposes", "semanticUri",
                   "sourceTaxonomyRef", "edmValueType", "edmAbstract", "edmConnects", "deviationReason"},
    "attribute": {"dataClassification", "edmMapsTo", "semanticUri", "valueDefinitions"},
}


# =========================================================================== shapes seen in samples

def kind_of_attribute(a: dict) -> str:
    return f"attribute:{a.get('type')}"


def walk_attributes(props, out):
    for a in props or []:
        if isinstance(a, dict):
            out.append(a)
            walk_attributes(a.get("properties"), out)
            items = a.get("items")
            walk_attributes(items if isinstance(items, list) else [items] if isinstance(items, dict) else [], out)


def shapes(model: dict) -> dict[str, set]:
    """Keys used per object kind in one model file."""
    seen: dict[str, set] = defaultdict(set)
    seen["model"] |= set(model)
    for b in model.get("buckets", []):
        seen["bucket"] |= set(b)
    for c in model.get("collections", []):
        seen["collection:" + ("derived" if c.get("refType") == "polyglot" else "defined")] |= set(c)
        attrs = []
        walk_attributes(c.get("properties"), attrs)
        for a in attrs:
            seen[kind_of_attribute(a)] |= set(a)
        for k in ("uniqueKey", "primaryKey", "Indxs"):
            for x in c.get(k) or []:
                if isinstance(x, dict):
                    seen[f"key:{k}"] |= set(x)
        for p in (c.get("referenceDiff") or {}).get("properties", []):
            seen["referenceDiff"] |= set(p)
    for r in model.get("relationships", []):
        seen["relationship"] |= set(r)
    for section in ("externalDefinitions", "polyglotDefinitions"):
        for d in (model.get(section) or {}).get("properties", []):
            seen[f"{section}:{d.get('definitionEntityType', 'entity')}"] |= set(d)
            attrs = []
            walk_attributes(d.get("properties"), attrs)
            for a in attrs:
                seen[kind_of_attribute(a)] |= set(a)
    for p in model.get("polyglotModelPaths", []) or []:
        seen["polyglotModelPath"] |= set(p)
    return seen


def sample_shapes(samples: Path) -> dict[str, set]:
    allowed: dict[str, set] = defaultdict(set)
    for f in samples.rglob("*.hck.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for k, v in shapes(data).items():
            allowed[k] |= v
    # a derived physical collection and a defined one share target properties
    allowed["collection:derived"] |= allowed["collection:defined"]
    # a jsonb array column has the properties of a jsonb object column (plugin type "json")
    allowed["attribute:jsonArray"] |= allowed["attribute:jsonObject"]
    # keys Studio writes on attributes of every type
    for kind in [k for k in allowed if k.startswith("attribute:")]:
        allowed[kind] |= {"description", "hackoladeMeta", "code", "isActivated", "GUID", "name"}
    return allowed


# =========================================================================== integrity

def integrity(path: Path, m: dict) -> list[str]:
    problems = []
    guids = defaultdict(int)

    def count(o):
        if isinstance(o, dict):
            if isinstance(o.get("GUID"), str):
                guids[o["GUID"]] += 1
            for k, v in o.items():
                # copies keep their source GUIDs; layout and lookup tables repeat GUIDs
                if k not in ("polyglotDefinitions", "externalDefinitions", "settings",
                             "idToNameHashTable", "hackoladeStyles"):
                    count(v)
        elif isinstance(o, list):
            for v in o:
                count(v)

    count(m)
    for g, n in guids.items():
        if n > 1:
            problems.append(f"GUID {g} used {n} times")

    colls = {c["GUID"]: c for c in m.get("collections", [])}
    buckets = {b["GUID"]: b for b in m.get("buckets", [])}
    sections = {s: {d["GUID"]: d for d in (m.get(s) or {}).get("properties", [])}
                for s in ("externalDefinitions", "polyglotDefinitions")}
    section_guid = {(m.get(s) or {}).get("GUID"): s for s in sections}

    def attrs_of(container: dict) -> dict:
        out = []
        walk_attributes(container.get("properties"), out)
        return {a["GUID"]: a for a in out if "GUID" in a}

    def field(path_: list) -> bool:
        if not path_ or path_[0] not in colls:
            return False
        c = colls[path_[0]]
        if c.get("refType") == "polyglot":
            copy = sections["polyglotDefinitions"].get(path_[1]) if len(path_) > 2 else None
            return copy is not None and path_[-1] in attrs_of(copy)
        return path_[-1] in attrs_of(c)

    for r in m.get("relationships", []):
        for end in ("parentCollection", "childCollection"):
            if r.get(end) not in colls:
                problems.append(f"relationship {r.get('name')}: {end} does not resolve")
        for end in ("parentField", "childField"):
            for p in r.get(end, []):
                if not field(p):
                    problems.append(f"relationship {r.get('name')}: {end} {p} does not resolve")

    for c in colls.values():
        name = c.get("collectionName")
        if c.get("bucketId") and c["bucketId"] not in buckets:
            problems.append(f"{name}: bucketId does not resolve")
        if c.get("refType") == "polyglot":
            if c.get("ref") not in sections["polyglotDefinitions"]:
                problems.append(f"{name}: derived entity's ref is not in polyglotDefinitions")
            rip = c.get("refIdPath", [])
            if len(rip) != 3 or rip[0] != m["GUID"] or section_guid.get(rip[1]) != "polyglotDefinitions":
                problems.append(f"{name}: refIdPath does not point into this model's polyglotDefinitions")
        own = attrs_of(c) if c.get("refType") != "polyglot" else \
            attrs_of(sections["polyglotDefinitions"].get(c.get("ref"), {}))
        for a in own.values():
            if a.get("refType") == "external":
                rip = a.get("refIdPath", [])
                if a.get("ref") not in sections["externalDefinitions"]:
                    problems.append(f"{name}.{a.get('name')}: external reference does not resolve")
                elif len(rip) != 3 or rip[0] != m["GUID"] or section_guid.get(rip[1]) != "externalDefinitions":
                    problems.append(f"{name}.{a.get('name')}: refIdPath is wrong")
            if c.get("refType") != "polyglot" and a.get("foreignCollection") and a["foreignCollection"] not in colls:
                problems.append(f"{name}.{a.get('name')}: foreignCollection does not resolve")
        for p in (c.get("referenceDiff") or {}).get("properties", []):
            if p["GUID"] not in own:
                problems.append(f"{name}: referenceDiff names an attribute that is not in the entity")
        for key in ("uniqueKey", "primaryKey"):
            for k in c.get(key) or []:
                for part in k.get("compositeUniqueKey", []) + k.get("compositePrimaryKey", []):
                    if part["keyId"] not in own:
                        problems.append(f"{name}: {key} column does not resolve")
        for ix in c.get("Indxs") or []:
            for col in ix.get("columns", []):
                if col["keyId"] not in own:
                    problems.append(f"{name}: index {ix.get('indxName')} column does not resolve")
    for b in buckets.values():
        for cid in b.get("collectionIds", []):
            if cid not in colls:
                problems.append(f"bucket {b.get('name')}: collectionId does not resolve")

    # linked files
    cache: dict[Path, dict] = {}
    for section, defs in sections.items():
        for d in defs.values():
            link = d.get("link")
            if not link:
                continue
            target = (path.parent / link).resolve()
            if not target.exists():
                problems.append(f"{section} {d.get('name') or d.get('collectionName')}: link {link} does not exist")
                continue
            src = cache.setdefault(target, json.loads(target.read_text(encoding="utf-8")))
            src_colls = {c["GUID"]: c for c in src.get("collections", [])}
            kind = d.get("definitionEntityType")
            nested = "/properties/" in d.get("fieldRelativePath", "")   # a normalised child table
            if section == "polyglotDefinitions" and kind == "collection" and not nested and d["GUID"] not in src_colls:
                problems.append(f"polyglot copy {d.get('collectionName')}: GUID is not an entity of {link}")
            if section == "externalDefinitions" and "/properties/" not in d.get("fieldRelativePath", ""):
                names = {c.get("collectionName") for c in src.get("collections", [])}
                if d.get("name") not in names:
                    problems.append(f"external definition {d.get('name')}: no such entity in {link}")
    for p in m.get("polyglotModelPaths", []) or []:
        if not (path.parent / p["polyglotModelPath"]).exists():
            problems.append(f"polyglotModelPath {p['polyglotModelPath']} does not exist")
    table = m.get("idToNameHashTable", {})
    for g in colls:
        if g not in table:
            problems.append(f"idToNameHashTable lacks entity {colls[g].get('collectionName')}")
    return problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--samples", type=Path, required=True, help="clone of hackolade/demo-models-read-only")
    ap.add_argument("files", nargs="*", type=Path)
    args = ap.parse_args(argv)
    files = args.files or sorted((REPO / "src").rglob("*.hck.json"))
    allowed = sample_shapes(args.samples)
    if not allowed:
        print(f"No sample models found under {args.samples}")
        return 2
    failed = 0
    for f in files:
        m = json.loads(f.read_text(encoding="utf-8"))
        problems = integrity(f, m)
        for kind, keys in shapes(m).items():
            extra = keys - allowed.get(kind, set())
            extra -= CUSTOM["model"] if kind == "model" else set()
            extra -= CUSTOM["collection"] if kind.startswith("collection") or kind.startswith("polyglotDefinitions") else set()
            extra -= CUSTOM["attribute"] if kind.startswith("attribute") else set()
            if extra:
                problems.append(f"{kind}: keys never seen in a Studio-saved sample: {sorted(extra)}")
        rel = f.relative_to(REPO) if f.is_relative_to(REPO) else f
        status = "ok" if not problems else f"{len(problems)} problem(s)"
        print(f"{rel}: {status}")
        for p in problems:
            print("   ", p)
        failed += bool(problems)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
