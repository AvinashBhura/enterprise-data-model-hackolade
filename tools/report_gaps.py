"""Brownfield gap report: an application's physical model against the Domain.

Spec 0005, requirement 14. Reads a reverse-engineered physical model whose
tables and columns carry the `edmMapsTo` custom property (the Domain entity,
or entity.attribute, each one holds), the Domain polyglot models they map to,
and optionally the compMod delta model, and writes a Markdown report:

1. tables and columns with no mapping;
2. mapped columns whose type or allowed values differ from the Domain attribute;
3. Domain attributes of mapped entities that no column holds;
4. (with --delta) the entities the delta model lists as different.

Usage:
    python tools/report_gaps.py --model APP.hck.json --domain DOMAIN.hck.json [--domain ...]
                                [--delta DELTA.hck.json] [--out gaps.md] [--fail-on-gaps]

Read-only. Exit code 0, or 1 with --fail-on-gaps when any gap is found.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from edm.model import norm_name  # noqa: E402

UUID_PREFIX = "^[0-9a-fA-F]{8}"


def category(a: dict) -> str:
    """A type family that a logical attribute and a physical column can share."""
    t, ct, mode = a.get("type"), a.get("childType"), a.get("mode")
    if ct == "uuid" or (t == "string" and str(a.get("pattern", "")).startswith(UUID_PREFIX)):
        return "uuid"
    if t in ("jsonObject", "jsonArray", "document", "array", "reference") or ct == "json":
        return "structured"
    if t == "numeric":
        return "integer" if (ct == "integer" or mode in ("integer", "int", "int32", "int64", "bigint", "smallint")) else "decimal"
    if t == "boolean":
        return "boolean"
    if ct == "date" or mode == "date":
        return "date"
    if ct in ("timestamp", "timestamp_tz", "timestamp_ntz", "datetime") or mode == "timestamp":
        return "datetime"
    if ct == "time" or mode == "time":
        return "time"
    return "text"


@dataclass
class Report:
    unmapped_tables: list[str] = field(default_factory=list)
    unmapped_columns: list[str] = field(default_factory=list)
    bad_mappings: list[str] = field(default_factory=list)
    mismatches: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    delta: list[str] = field(default_factory=list)

    @property
    def gaps(self) -> int:
        return sum(len(x) for x in (self.unmapped_tables, self.unmapped_columns, self.bad_mappings,
                                    self.mismatches, self.missing))

    def markdown(self, title: str) -> str:
        def section(name, items, empty="None."):
            body = "\n".join(f"- {i}" for i in items) if items else empty
            return f"## {name} ({len(items)})\n\n{body}\n"
        parts = [f"# Gap report: {title}\n",
                 f"{self.gaps} gap(s).\n",
                 section("Tables with no mapping", self.unmapped_tables),
                 section("Columns with no mapping", self.unmapped_columns),
                 section("Mappings that name nothing in the Domain", self.bad_mappings),
                 section("Mapped columns that differ from the Domain", self.mismatches),
                 section("Domain attributes with no column", self.missing)]
        if self.delta:
            parts.append(section("Entities the compMod delta lists", self.delta))
        return "\n".join(parts)


def _columns(model: dict, entity: dict) -> list[dict]:
    """A table's columns: its own, or those of its copy when it is derived."""
    if entity.get("refType") == "polyglot":
        for d in (model.get("polyglotDefinitions") or {}).get("properties", []):
            if d.get("GUID") == entity.get("ref"):
                return d.get("properties", [])
    return entity.get("properties", [])


def domain_index(models: list[dict]) -> dict[str, dict]:
    """{normalised entity name: {"name":..., "attrs": {attr name: attr}}} for defined entities."""
    out = {}
    for m in models:
        for c in m.get("collections", []):
            if c.get("refType"):
                continue
            out[norm_name(c["collectionName"])] = {
                "name": c["collectionName"],
                "attrs": {a["name"]: a for a in c.get("properties", []) if a.get("name")},
            }
    return out


def report(app: dict, domains: list[dict], delta: dict | None = None) -> Report:
    r = Report()
    index = domain_index(domains)
    covered: dict[str, set] = {}   # Domain entity key -> attribute names held by some column
    for t in app.get("collections", []):
        table = t.get("code") or t.get("collectionName")
        t_map = (t.get("edmMapsTo") or "").strip()
        if not t_map:
            r.unmapped_tables.append(f"`{table}`")
        elif norm_name(t_map.split(".")[0]) not in index:
            r.bad_mappings.append(f"`{table}` → `{t_map}`: no such Domain entity")
        for col in _columns(app, t):
            name = col.get("code") or col.get("name")
            c_map = (col.get("edmMapsTo") or "").strip()
            if not c_map:
                r.unmapped_columns.append(f"`{table}.{name}`")
                continue
            ent_name, _, attr_name = c_map.partition(".")
            if not attr_name and t_map:
                ent_name, attr_name = t_map.split(".")[0], c_map
            ent = index.get(norm_name(ent_name))
            attr = ent["attrs"].get(attr_name) if ent else None
            if attr is None:
                r.bad_mappings.append(f"`{table}.{name}` → `{c_map}`: no such Domain attribute")
                continue
            covered.setdefault(norm_name(ent_name), set()).add(attr_name)
            if category(col) != category(attr):
                r.mismatches.append(f"`{table}.{name}` is {category(col)}; `{ent['name']}.{attr_name}` is {category(attr)}")
            if isinstance(attr.get("enum"), list) and attr["enum"]:
                col_values = col.get("enum") if isinstance(col.get("enum"), list) else None
                if col_values is None:
                    r.mismatches.append(f"`{table}.{name}` has no list of allowed values; `{ent['name']}.{attr_name}` "
                                        f"allows {attr['enum']}")
                elif set(col_values) != set(attr["enum"]):
                    extra = sorted(set(col_values) - set(attr["enum"]))
                    lacking = sorted(set(attr["enum"]) - set(col_values))
                    r.mismatches.append(f"`{table}.{name}` allowed values differ from `{ent['name']}.{attr_name}` "
                                        f"(extra {extra}, missing {lacking})")
    mapped_entities = {norm_name((t.get("edmMapsTo") or "").split(".")[0]) for t in app.get("collections", [])
                       if t.get("edmMapsTo")} | set(covered)
    for key in sorted(mapped_entities):
        ent = index.get(key)
        if not ent:
            continue
        for attr_name in ent["attrs"]:
            if attr_name not in covered.get(key, set()):
                r.missing.append(f"`{ent['name']}.{attr_name}`")
    if delta:
        r.delta = sorted(f"`{c.get('collectionName')}`" for c in delta.get("collections", []))
    return r


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", type=Path, required=True, help="reverse-engineered application model")
    ap.add_argument("--domain", type=Path, action="append", required=True, help="Domain polyglot model (repeatable)")
    ap.add_argument("--delta", type=Path, help="compMod delta model (optional)")
    ap.add_argument("--out", type=Path, help="write the report here instead of printing it")
    ap.add_argument("--fail-on-gaps", action="store_true")
    args = ap.parse_args(argv)
    load = lambda p: json.loads(p.read_text(encoding="utf-8"))  # noqa: E731
    app = load(args.model)
    r = report(app, [load(p) for p in args.domain], load(args.delta) if args.delta else None)
    text = r.markdown(app.get("modelName", args.model.stem))
    if args.out:
        args.out.write_text(text, encoding="utf-8")
        print(f"{r.gaps} gap(s); report written to {args.out}")
    else:
        print(text)
    return 1 if (args.fail_on_gaps and r.gaps) else 0


if __name__ == "__main__":
    sys.exit(main())
