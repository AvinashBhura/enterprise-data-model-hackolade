"""List every difference between the LinkML classes and the migrated Hackolade entities.

Spec 0002 acceptance criterion 1, spec 0003 criterion 2, spec 0004 criterion 2.
Each difference is either explained (a change approved in D2, D3, D12 or a
spec, named in the output) or UNEXPLAINED. Exits non-zero if any difference is
unexplained.

Usage:
    python migration/compare.py --tag linkml-final-v0.5.0 [--scope SCOPE]
    python migration/compare.py --linkml-src DIR [--scope SCOPE]

SCOPE: all (default), common, foundation, HR, process-core, application.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))

from build import SIMPLE, linkml_from_tag  # noqa: E402
from linkml_source import Schema  # noqa: E402

SCOPES = {
    "common": "src/01_foundation/common/",
    "foundation": "src/01_foundation/Foundation",
    "HR": "src/02_domain/HR/",
    "process-core": "src/03_process/_core/",
    "application": "src/04_application/_shared/",
}


def ws(text) -> str:
    return " ".join(str(text or "").split())


def describe(a: dict) -> str:
    return a.get("description") or a.get("refDescription") or ""


def kind_of(a: dict) -> str:
    t, ct = a.get("type"), a.get("childType")
    if t == "reference":
        return "value:" + a["$ref"].rsplit("/", 1)[-1]
    if t == "array":
        items = a.get("properties") or a.get("items") or [{}]
        return "array<" + kind_of(items[0]) + ">"
    if t == "document":
        return "object"
    if ct == "enum":
        return "enum"
    if t == "string" and a.get("pattern", "").startswith("^[0-9a-fA-F]{8}"):
        return "uuid"
    if t == "string" and a.get("format") == "uri":
        return "uri"
    return {"varchar": "string", "date": "date", "timestamp_tz": "datetime", "time": "time",
            "number": "decimal", "integer": "integer", "boolean": "boolean"}.get(ct, f"{t}/{ct}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tag", default="linkml-final-v0.5.0")
    ap.add_argument("--linkml-src", type=Path)
    ap.add_argument("--linkml-repo", type=Path, help="clone of the LinkML repository holding the tag (D13)")
    ap.add_argument("--repo", type=Path, default=REPO)
    ap.add_argument("--scope", default="all", choices=["all", *SCOPES])
    args = ap.parse_args(argv)
    cfg = yaml.safe_load((HERE / "models.yaml").read_text(encoding="utf-8"))
    mp = cfg["mapping"]
    schema = Schema(args.linkml_src or linkml_from_tag(args.tag, args.linkml_repo))
    rows, unexplained = [], 0

    def row(entity, attr, status, note):
        nonlocal unexplained
        rows.append((entity, attr, status, note))
        if status == "UNEXPLAINED":
            unexplained += 1

    for mcfg in cfg["models"]:
        if args.scope != "all" and not mcfg["file"].startswith(SCOPES[args.scope]):
            continue
        path = args.repo / mcfg["file"]
        if not path.exists():
            row(mcfg["name"], "", "UNEXPLAINED", f"model file {mcfg['file']} does not exist")
            continue
        model = json.loads(path.read_text(encoding="utf-8"))
        entities = {c["collectionName"]: c for c in model["collections"] if not c.get("refType")}
        for ecfg in mcfg["entities"]:
            if not ecfg.get("linkml"):
                continue
            cls = schema.classes[ecfg["linkml"]]
            e = entities.get(cls.name)
            if e is None:
                row(cls.name, "", "UNEXPLAINED", "entity missing")
                continue
            ent_over = mp.get("entity_description_overrides", {}).get(cls.name)
            if ent_over and ws(e.get("description")) == ws(ent_over):
                row(cls.name, "(description)", "explained", "reworded without schema-language terms (models.yaml)")
            elif ws(e.get("description")) != ws(ecfg.get("description") or cls.description):
                row(cls.name, "(description)", "UNEXPLAINED", "entity description differs from LinkML")
            attrs = {a["name"]: a for a in e["properties"]}
            seen = set()
            for slot in schema.induced(cls.name).values():
                key, owner_key = f"{cls.name}.{slot.name}", f"{slot.owner}.{slot.name}"
                dropped = mp.get("dropped_attributes", {})
                reason = dropped.get(slot.name) or dropped.get(key) or dropped.get(owner_key)
                rng = (mp.get("range_overrides", {}).get(key) or mp.get("range_overrides", {}).get(owner_key)
                       or slot.range)
                if reason:
                    row(cls.name, slot.name, "explained", f"removed: {reason}")
                    continue
                if rng in mp.get("dropped_ranges", []):
                    row(cls.name, slot.name, "explained", "removed: Classifiable is a marker (spec 0002, resolved question 1)")
                    continue
                if rng in mp["polymorphic_ranges"] and not slot.multivalued:
                    names = [f"{slot.name}_entity_type", f"{slot.name}_entity_id"]
                    missing = [n for n in names if n not in attrs]
                    seen.update(names)
                    if missing:
                        row(cls.name, slot.name, "UNEXPLAINED", f"pair attributes missing: {missing}")
                    else:
                        row(cls.name, slot.name, "explained",
                            f"range {rng} became the pair {names[0]} + {names[1]} (spec 0002 requirement 14)")
                        over = (mp.get("description_overrides", {}).get(key)
                                or mp.get("description_overrides", {}).get(owner_key))
                        if ws(describe(attrs[names[1]])) not in (ws(slot.description), ws(over)):
                            row(cls.name, names[1], "UNEXPLAINED", "description differs")
                    continue
                a = attrs.get(slot.name)
                seen.add(slot.name)
                if a is None:
                    row(cls.name, slot.name, "UNEXPLAINED", "attribute missing")
                    continue
                notes = []
                # type
                got = kind_of(a)
                iso = mp["iso_code_lists"].get(rng)
                if iso:
                    want = "array<string>" if slot.multivalued else "string"
                    if got != want or (a.get("pattern") if not slot.multivalued else a["properties"][0].get("pattern")) != iso["pattern"]:
                        row(cls.name, slot.name, "UNEXPLAINED", f"expected {want} with pattern {iso['pattern']}")
                    else:
                        notes.append(f"{rng} became a format rule (D3)")
                elif rng in schema.enums:
                    values = list(schema.enums[rng].values)
                    got_values = a.get("enum") if not slot.multivalued else None
                    usage = cls.slot_usage.get(slot.name) or {}
                    if usage.get("equals_string"):
                        values = [usage["equals_string"]]
                        notes.append(f"enum narrowed to {values} (LinkML equals_string)")
                    if got_values != values:
                        added = [v for v in (got_values or []) if v not in values]
                        removed = [v for v in values if v not in (got_values or [])]
                        if not removed and added and slot.name in (ecfg.get("enum_additions") or {}):
                            notes.append(f"enum values added: {added} (spec 0002, Talent Acquisition roles)")
                        elif not removed and added and cls.name != slot.owner:
                            notes.append(f"enum values added at the Foundation: {added}")
                        else:
                            row(cls.name, slot.name, "UNEXPLAINED", f"enum differs (added {added}, removed {removed})")
                    else:
                        notes.append("enum moved onto the attribute (D3)")
                elif rng in mp["value_types"]:
                    want = f"array<value:{rng}>" if slot.multivalued else f"value:{rng}"
                    if got != want:
                        row(cls.name, slot.name, "UNEXPLAINED", f"expected {want}, found {got}")
                elif rng in mp.get("inline_classes", []):
                    if got != "array<object>":
                        row(cls.name, slot.name, "UNEXPLAINED", f"expected array<object>, found {got}")
                    else:
                        notes.append(f"{rng} written inline (D12)")
                elif rng in mp["polymorphic_ranges"]:
                    if got != "array<object>":
                        row(cls.name, slot.name, "UNEXPLAINED", f"expected an array of pairs, found {got}")
                    else:
                        notes.append("array of entity-type + entity-id pairs (spec 0002 requirement 14)")
                elif rng in schema.classes:
                    want = "array<uuid>" if slot.multivalued else "uuid"
                    if got != want:
                        row(cls.name, slot.name, "UNEXPLAINED", f"expected {want}, found {got}")
                    elif slot.multivalued:
                        notes.append(f"list of {rng} entity_id values")
                    elif not a.get("relationshipType"):
                        row(cls.name, slot.name, "UNEXPLAINED", f"reference to {rng} has no relationship")
                    elif owner_key in mp.get("self_references", []) and cls.name != slot.owner:
                        notes.append(f"relationship to {cls.name} itself (models.yaml self_references)")
                    else:
                        notes.append(f"relationship to {rng}")
                else:
                    base = SIMPLE.get(rng) or ("uuid" if rng == "uuid" else "string")
                    want = f"array<{base}>" if slot.multivalued else base
                    if slot.name == "entity_id":
                        want = "uuid"
                    if got != want:
                        row(cls.name, slot.name, "UNEXPLAINED", f"expected {want}, found {got}")
                # required
                if bool(a.get("required")) != bool(slot.required):
                    row(cls.name, slot.name, "UNEXPLAINED", f"required {bool(a.get('required'))}, LinkML {slot.required}")
                # description
                desc = ws(describe(a))
                over = mp.get("description_overrides", {}).get(key) or mp.get("description_overrides", {}).get(owner_key)
                if over and desc == ws(over):
                    notes.append("description reworded without schema-language terms (models.yaml)")
                elif desc != ws(slot.description):
                    pr = mp.get("patterns", {}).get(key) or mp.get("patterns", {}).get(owner_key)
                    std = (iso or pr or {}).get("standard")
                    if std and desc == ws(f"{slot.description} Format: {std}."):
                        notes.append("standard named in the description (D3)")
                    else:
                        row(cls.name, slot.name, "UNEXPLAINED", "description differs")
                if notes:
                    row(cls.name, slot.name, "explained", "; ".join(notes))
            new_names = {x["name"] for x in ecfg.get("attributes", []) + ecfg.get("prepend", [])}
            for name in attrs:
                if name in seen:
                    continue
                if name in new_names:
                    row(cls.name, name, "explained", "added (models.yaml, approved spec)")
                else:
                    row(cls.name, name, "UNEXPLAINED", "attribute not in LinkML")

    width = max((len(f"{r[0]}.{r[1]}") for r in rows), default=10)
    for entity, attr, status, note in rows:
        label = f"{entity}.{attr}" if attr else entity
        print(f"{label:<{width}}  {status:<11}  {note}")
    print(f"\n{len(rows)} difference(s), {unexplained} unexplained")
    return 1 if unexplained else 0


if __name__ == "__main__":
    sys.exit(main())
