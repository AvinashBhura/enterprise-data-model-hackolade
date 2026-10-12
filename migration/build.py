"""One-time builder: write the EDM's Hackolade models (D5, D12).

Reads the LinkML schemas at tag linkml-final-v0.5.0 and migration/models.yaml,
and writes the polyglot models listed there, then the Candidate Journey physical
model (migration/physical.py). Each written file is opened and saved in
Hackolade Studio before it is trusted (docs/workflows/studio-verification.md).

Never overwrites: if any target file exists, nothing is written (spec 0002,
requirement 6). Use --out to build into another folder, for example to compare
a rebuild with the committed files.

The LinkML schemas are read from tag linkml-final-v0.5.0 of the earlier
repository, AvinashBhura/enterprise-data-model (D13): clone it next to this one,
or pass --linkml-repo or --linkml-src.

Usage:
    python migration/build.py                       # LinkML read from the git tag
    python migration/build.py --linkml-src DIR      # LinkML read from an extracted src/ folder
    python migration/build.py --out /tmp/edm-build  # write somewhere else
"""

from __future__ import annotations

import argparse
import copy
import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))

import hackolade_file as hf  # noqa: E402
from linkml_source import BUILTIN_TYPES, Schema, Slot  # noqa: E402

ENTITY_CUSTOM_KEYS = ("layer", "foundationKind", "entityType", "steward", "edmComposes",
                      "semanticUri", "sourceTaxonomyRef", "edmValueType", "edmAbstract",
                      "edmConnects", "deviationReason")
BASE_TYPES = ["Entity", "Identifiable", "Lifecycleable", "Temporal", "Addressable", "RoleHolder",
              "Classifiable"]
SIMPLE = {"string": "string", "integer": "integer", "decimal": "decimal", "float": "decimal",
          "double": "decimal", "boolean": "boolean", "date": "date", "datetime": "datetime",
          "time": "time", "uri": "uri", "uriorcurie": "uri", "uuid": "uuid"}


def snake(name: str) -> str:
    out = ""
    for i, ch in enumerate(name):
        if ch.isupper() and i and (not name[i - 1].isupper() or
                                   (i + 1 < len(name) and name[i + 1].islower())):
            out += "_"
        out += ch.lower()
    return out.replace(" ", "_")


def rel_link(from_file: str, to_file: str) -> str:
    return os.path.relpath(to_file, os.path.dirname(from_file)).replace(os.sep, "/")


# =========================================================================== attribute specs

class Specs:
    """Turns LinkML slots and models.yaml attributes into one attribute-spec form."""

    def __init__(self, schema: Schema, mapping: dict):
        self.schema = schema
        self.m = mapping

    def from_slot(self, cls: str, slot: Slot) -> dict | None:
        key, owner_key = f"{cls}.{slot.name}", f"{slot.owner}.{slot.name}"
        dropped = self.m.get("dropped_attributes", {})
        if slot.name in dropped or key in dropped or owner_key in dropped:
            return None
        rng = (self.m.get("range_overrides", {}).get(key)
               or self.m.get("range_overrides", {}).get(owner_key) or slot.range)
        if rng in self.m.get("dropped_ranges", []):
            return None
        desc_over = self.m.get("description_overrides", {})
        description = " ".join((desc_over.get(key) or desc_over.get(owner_key) or slot.description).split())
        spec = {"name": slot.name, "required": slot.required, "description": description,
                "many": slot.multivalued, "pk": slot.identifier, "source": "linkml",
                "semantic_uri": self.schema.expand_uri(slot.slot_uri) if slot.slot_uri else None}
        if slot.pattern:
            spec["pattern"] = slot.pattern
        iso = self.m["iso_code_lists"].get(rng)
        pattern_rule = self.m.get("patterns", {}).get(key) or self.m.get("patterns", {}).get(owner_key)
        if iso:
            spec.update(kind="string", pattern=iso["pattern"], standard=iso["standard"])
        elif rng in self.schema.enums:
            enum = self.schema.enums[rng]
            spec.update(kind="enum", values=dict(enum.values))
        elif rng in self.m["value_types"]:
            spec.update(kind="value", target=rng)
        elif rng in self.m.get("inline_classes", []):
            fields = [self.from_slot(rng, s) for s in self.schema.induced(rng).values()]
            spec.update(kind="object", fields=[f for f in fields if f])
        elif rng in self.m["polymorphic_ranges"]:
            allowed = (self.m.get("polymorphic_allowed", {}).get(key)
                       or self.m.get("polymorphic_allowed", {}).get(owner_key)
                       or self.m["polymorphic_ranges"][rng])
            spec.update(kind="pair", allowed=list(allowed))
        elif rng in self.schema.classes:
            spec.update(kind="ref", target=rng)
        elif rng in SIMPLE:
            spec.update(kind=SIMPLE[rng])
        elif rng in self.schema.types:
            base = self.schema.types[rng].get("base", "str")
            spec.update(kind="string" if base == "str" else SIMPLE.get(base, "string"))
            if self.schema.types[rng].get("pattern"):
                spec["pattern"] = self.schema.types[rng]["pattern"]
        else:
            raise ValueError(f"{key}: unknown range {rng}")
        if spec["name"] == "entity_id" or rng == "uuid":
            spec["kind"] = "uuid"
            spec.pop("pattern", None)
        if pattern_rule:
            spec.update(pattern=pattern_rule["pattern"], standard=pattern_rule["standard"])
        return spec

    @staticmethod
    def from_yaml(raw: dict) -> dict:
        for v in raw.get("values", {}) or {}:
            if not isinstance(v, str):
                raise ValueError(f"{raw['name']}: enum value {v!r} is not text; quote it in models.yaml")
        spec = dict(raw)
        spec.setdefault("required", False)
        spec.setdefault("description", "")
        spec.setdefault("many", False)
        spec["source"] = "new"
        return spec


# =========================================================================== one model

class ModelBuilder:
    def __init__(self, build: "Build", cfg: dict):
        self.b = build
        self.cfg = cfg
        self.file = cfg["file"]
        custom = {"edmLayer": cfg["layer"]}
        if cfg.get("domain"):
            custom["edmDomain"] = cfg["domain"]
        if cfg.get("subdomain"):
            custom["edmSubdomain"] = cfg["subdomain"]
        self.m = hf.new_model(cfg["name"], " ".join(cfg["description"].split()), **custom)
        self.bucket = hf.add_bucket(self.m, cfg["name"], self.m["description"])
        self.pending: list[tuple] = []        # (entity, attr dict, target, target_attribute, required)
        self.local: dict[str, dict] = {}      # entity name -> collection
        self.derived: dict[str, dict] = {}    # entity name -> derived collection

    # ------------------------------------------------------------------ helpers

    def g(self, *parts) -> str:
        return hf.gid(self.m["modelName"], *parts)

    def value_def(self, name: str) -> dict:
        src_model, src_file = self.b.built["CommonValueTypes"]
        src = next(c for c in src_model["collections"] if c["collectionName"] == name)
        return hf.external_definition(self.m, rel_link(self.file, src_file), src_model, src,
                                      ENTITY_CUSTOM_KEYS)

    def field_custom(self, entity: str, spec: dict) -> dict:
        out = {}
        cls = self.b.mapping.get("classification", {}).get(f"{entity}.{spec['name']}")
        if cls:
            out["dataClassification"] = cls
        if spec.get("semantic_uri"):
            out["semanticUri"] = spec["semantic_uri"]
        if spec.get("values"):
            out["valueDefinitions"] = "\n".join(f"{k}: {v}" if v else k for k, v in spec["values"].items())
        return out

    # ------------------------------------------------------------------ materialise

    def make(self, entity: str, spec: dict, path: str, nested: bool = False) -> list[dict]:
        """Attribute dict(s) for one spec. Records foreign keys for later."""
        kind, name = spec["kind"], spec["name"]
        desc = spec.get("description", "")
        if spec.get("standard"):
            desc = (desc + " " if desc else "") + f"Format: {spec['standard']}."
        req = bool(spec.get("required"))
        g = lambda *p: self.g(entity, path, *p)  # noqa: E731

        if kind == "pair":
            allowed = spec["allowed"]
            if spec.get("many"):
                single = self.b.mapping.get("singular", {}).get(name, name.rstrip("s"))
                fields = [
                    hf.scalar(g(name, "item", f"{single}_entity_type"), f"{single}_entity_type", "enum",
                              f"Entity type of the {single.replace('_', ' ')}: one of "
                              f"{', '.join(allowed)}.", True, values=allowed),
                    hf.scalar(g(name, "item", f"{single}_entity_id"), f"{single}_entity_id", "uuid",
                              f"entity_id of the {single.replace('_', ' ')}.", True),
                ]
                for extra in self.b.mapping.get("pair_extras", {}).get(name, []):
                    fields.append(hf.scalar(g(name, "item", extra["name"]), extra["name"], extra["kind"],
                                            extra["description"]))
                item = hf.obj(g(name, "item"), None, fields)
                return [hf.array(g(name), name, item, desc, req)]
            t = hf.scalar(g(f"{name}_entity_type"), f"{name}_entity_type", "enum",
                          f"Entity type of {name.replace('_', ' ')}: one of {', '.join(allowed)}. "
                          f"Polymorphic reference: no relationship (docs/patterns/polymorphic_references.md).",
                          req, values=allowed)
            i = hf.scalar(g(f"{name}_entity_id"), f"{name}_entity_id", "uuid", desc, req)
            return [t, i]

        if kind == "value":
            ext = self.value_def(spec["target"])
            if spec.get("many"):
                item = hf.ext_ref(g(name, "item"), None, self.m, ext)
                return [hf.array(g(name), name, item, desc, req)]
            return [hf.ext_ref(g(name), name, self.m, ext, desc, req)]

        if kind == "object":
            fields = []
            for f in spec["fields"]:
                fields += self.make(entity, f, f"{path}/{name}/item", nested=True)
            if spec.get("many"):
                return [hf.array(g(name), name, hf.obj(g(name, "item"), None, fields), desc, req)]
            return [hf.obj(g(name), name, fields, desc, req)]

        if kind == "ref":
            if spec.get("many"):
                item = hf.scalar(g(name, "item"), None, "uuid")
                return [hf.array(g(name), name, item, desc, req)]
            a = hf.scalar(g(name), name, "uuid", desc, req, pk=bool(spec.get("pk")),
                          extra=self.field_custom(entity, spec))
            if not nested:  # a nested reference has no relationship (D12)
                self.pending.append((entity, a, spec["target"], spec.get("target_attribute"), req))
            return [a]

        extra = self.field_custom(entity, spec)
        if spec.get("many"):
            item = hf.scalar(g(name, "item"), None, kind, pattern=spec.get("pattern"),
                             values=list(spec.get("values", {})) or None)
            return [hf.array(g(name), name, item, desc, req) | extra]
        return [hf.scalar(g(name), name, kind, desc, req, pk=bool(spec.get("pk")),
                          pattern=spec.get("pattern"),
                          values=list(spec.get("values", {})) if kind == "enum" else None,
                          extra=extra)]

    # ------------------------------------------------------------------ carried Foundation attributes (D12)

    def carried(self, entity: str, kind: str) -> tuple[list[dict], dict]:
        """Copies of the Foundation kind's attributes, with new GUIDs and references
        rebound to this model. Returns (attributes, kind collection)."""
        f_model, _ = self.b.built["Foundation"]
        src = next(c for c in f_model["collections"] if c["collectionName"] == kind)
        out = []
        for a in src["properties"]:
            c = copy.deepcopy(a)
            self._regid(c, entity, c["name"])
            self._rebind(c)
            for k in hf.FK_KEYS:
                c.pop(k, None)
            target = self.b.fk_targets.get(("Foundation", kind, a["name"]))
            if target:
                t_entity, t_attr = target
                if f"{kind}.{a['name']}" in self.b.mapping.get("self_references", []):
                    t_entity = entity         # a JobRequisition replaces a JobRequisition
                self.pending.append((entity, c, t_entity, t_attr, bool(c.get("required"))))
            out.append(c)
        return out, src

    def _regid(self, a: dict, entity: str, path: str) -> None:
        a["GUID"] = self.g(entity, "carried", path)
        for i, child in enumerate(a.get("properties", []) or []):
            self._regid(child, entity, f"{path}/{child.get('name') or i}")

    def _rebind(self, a: dict) -> None:
        if a.get("type") == "reference" and a.get("refType") == "external":
            ext = self.value_def(a["$ref"].rsplit("/", 1)[-1])
            a.update(ref=ext["GUID"],
                     refIdPath=[self.m["GUID"], self.m["externalDefinitions"]["GUID"], ext["GUID"]])
        for child in a.get("properties", []) or []:
            self._rebind(child)

    # ------------------------------------------------------------------ entities

    def build_entity(self, ecfg: dict) -> dict:
        b = self.b
        layer = self.cfg["layer"]
        name = ecfg.get("name") or ecfg["linkml"]
        cls = b.schema.classes.get(ecfg["linkml"]) if ecfg.get("linkml") else None
        kind = ecfg.get("kind")
        ent_over = b.mapping.get("entity_description_overrides", {})
        description = " ".join((ecfg.get("description") or ent_over.get(name)
                                or (cls.description if cls else "")).split())
        props: list[dict] = []
        composes: list[str] = []

        if kind:                                     # Domain, Process, Application entity
            props, kind_coll = self.carried(name, kind)
            composes = list(kind_coll.get("edmComposes", []))
            by_name = {p["name"]: i for i, p in enumerate(props)}
            own_specs = []
            if cls:
                kind_names = set(by_name)
                for slot in b.schema.induced(cls.name).values():
                    spec = b.specs.from_slot(cls.name, slot)
                    if spec is None:
                        continue
                    produced = ([f"{spec['name']}_entity_type", f"{spec['name']}_entity_id"]
                                if spec["kind"] == "pair" and not spec["many"] else [spec["name"]])
                    if any(n in kind_names for n in produced):
                        if spec["kind"] == "pair" and not spec["many"]:
                            for n in produced:          # inherited pair: only required may change
                                props[by_name[n]]["required"] = props[by_name[n]].get("required") or spec["required"]
                        else:
                            self._apply_override(name, cls, slot, spec, props, by_name)
                    else:
                        own_specs.append(spec)
                for mix in cls.mixins:
                    if mix in BASE_TYPES and mix not in composes:
                        composes.append(mix)
                for usage_name, usage in cls.slot_usage.items():
                    if usage and usage.get("equals_string") and usage_name in by_name:
                        self._narrow(props[by_name[usage_name]], [usage["equals_string"]])
            own_specs += [b.specs.from_yaml(a) for a in ecfg.get("attributes", [])]
            for attr, values in (ecfg.get("narrow") or {}).items():
                self._narrow(props[by_name[attr]], values)
            for attr in ecfg.get("require") or []:
                props[by_name[attr]]["required"] = True
            if ecfg.get("lifecycle"):
                self._set_enum(props[by_name["lifecycle_state"]], ecfg["lifecycle"])
            for attr, enum_cfg in (ecfg.get("close_to_enum") or {}).items():
                a = props[by_name[attr]]
                self._set_enum(a, enum_cfg["values"])
                if enum_cfg.get("description"):
                    a["description"] = enum_cfg["description"]
            own = []
            for spec in own_specs:
                own += self.make(name, spec, "")
            # natural key first among the entity's own attributes
            props = props[:1] + own + props[1:] if ecfg.get("linkml") is None else props + own
            foundation_kind = kind
        else:                                        # Common, Foundation, technical entity
            specs = [b.specs.from_yaml(a) for a in ecfg.get("prepend", [])]
            if cls:
                for slot in b.schema.induced(cls.name).values():
                    spec = b.specs.from_slot(cls.name, slot)
                    if spec:
                        specs.append(spec)
            specs += [b.specs.from_yaml(a) for a in ecfg.get("attributes", [])]
            for spec in specs:
                props += self.make(name, spec, "")
            if layer == "Foundation":
                foundation_kind = name
                chain = b.schema.ancestors(cls.name)
                composes = ["Entity"]
                for c_name in chain:
                    for mix in b.schema.classes[c_name].mixins:
                        if mix in BASE_TYPES and mix not in composes:
                            composes.append(mix)
                for attr, extra_values in (ecfg.get("enum_additions") or {}).items():
                    a = next(p for p in props if p["name"] == attr)
                    a["enum"] = a["enum"] + list(extra_values)
                    a["valueDefinitions"] += "\n" + "\n".join(f"{k}: {v}" for k, v in extra_values.items())
            else:
                foundation_kind = "none"
                if any(p["name"] == "entity_id" for p in props):
                    composes = ["Entity"]
        custom = {
            "layer": layer,
            "foundationKind": foundation_kind,
            "entityType": ecfg["entityType"],
            "steward": ecfg.get("steward") or self.cfg["steward"],
            "edmComposes": [c for c in BASE_TYPES if c in composes],
            "semanticUri": b.schema.expand_uri(cls.class_uri) if cls and cls.class_uri else None,
            "sourceTaxonomyRef": ecfg.get("taxonomy"),
            "edmValueType": True if ecfg.get("valueType") else None,
            "edmAbstract": True if ecfg.get("abstract") else None,
            "edmConnects": ";".join(ecfg["connects"]) if ecfg.get("connects") else None,
        }
        coll = hf.add_entity(self.m, self.bucket, name, description, props, custom)
        self.local[name] = coll
        b.owner[name] = self.cfg["name"]
        # keys
        for p in props:
            spec_unique = any(a.get("name") == p["name"] and a.get("unique") for a in ecfg.get("attributes", []))
            if spec_unique:
                hf.add_unique_key(self.m, coll, [p], f"{snake(name)}_{p['name']}_uk")
        for combo in ecfg.get("unique", []) or []:
            attrs = [next(p for p in props if p["name"] == n) for n in combo]
            hf.add_unique_key(self.m, coll, attrs, f"{snake(name)}_{'_'.join(combo)}_uk")
        if ecfg.get("composite_pk"):
            attrs = [next(p for p in props if p["name"] == n) for n in ecfg["composite_pk"]]
            hf.add_composite_pk(self.m, coll, attrs, f"{snake(name)}_pk")
        return coll

    def _apply_override(self, entity, cls, slot, spec, props, by_name):
        """A LinkML class changes an attribute it inherits from its Foundation kind."""
        i = by_name[spec["name"]]
        current = props[i]
        if spec["name"] == "lifecycle_state" and spec.get("kind") == "enum":
            if list(spec["values"]) != current.get("enum"):
                self._set_enum(current, spec["values"])
            current["required"] = current.get("required") or spec["required"]
            return
        if slot.owner == cls.name:                   # redefined on the class itself
            new = self.make(entity, spec, "")
            if len(new) == 1:
                new[0]["GUID"] = current["GUID"]
                for k in ("relationshipType", "foreignCollection", "foreignField"):
                    new[0].pop(k, None)
                # keep the pending foreign key pointing at the attribute now in place
                self.pending = [(e, new[0] if a is current else a, t, ta, r)
                                for e, a, t, ta, r in self.pending]
                props[i] = new[0]
            return
        if spec["required"] and not current.get("required"):
            current["required"] = True

    @staticmethod
    def _narrow(attr: dict, values: list[str]) -> None:
        attr["enum"] = [v for v in attr["enum"] if v in values]
        missing = [v for v in values if v not in attr["enum"]]
        if missing:
            raise ValueError(f"{attr['name']}: {missing} are not Foundation values")
        lines = [l for l in attr.get("valueDefinitions", "").splitlines() if l.split(":")[0] in values]
        attr["valueDefinitions"] = "\n".join(lines)

    @staticmethod
    def _set_enum(attr: dict, values: dict) -> None:
        bad = [v for v in values if not isinstance(v, str)]
        if bad:
            raise ValueError(f"{attr['name']}: enum values {bad} are not text; quote them in models.yaml")
        attr.update(type="string", childType="enum", enum=list(values))
        attr.pop("pattern", None)
        attr["valueDefinitions"] = "\n".join(f"{k}: {v}" if v else k for k, v in values.items())

    # ------------------------------------------------------------------ relationships

    def resolve(self) -> None:
        for entity, attr, target, target_attr, required in self.pending:
            child = self.local[entity]
            if target in self.local:
                parent = self.local[target]
                parent_attr = self._key(parent["properties"], target_attr)
                path = [parent["GUID"], parent_attr["GUID"]]
            else:
                parent = self._derive(target)
                src_model, _ = self.b.built[self.b.owner[target]]
                src = next(c for c in src_model["collections"] if c["collectionName"] == target)
                parent_attr = self._key(src["properties"], target_attr)
                path = [parent["GUID"], src["GUID"], parent_attr["GUID"]]
            hf.relate(self.m, f"fk_{snake(entity)}_{attr['name']}", parent, path, child, attr, required)
            self.b.fk_targets[(self.cfg["name"], entity, attr["name"])] = (target, target_attr)

    @staticmethod
    def _key(props: list[dict], name: str | None) -> dict:
        if name:
            return next(p for p in props if p["name"] == name)
        return next(p for p in props if p.get("primaryKey"))

    def _derive(self, target: str) -> dict:
        if target in self.derived:
            return self.derived[target]
        owner = self.b.owner[target]
        src_model, src_file = self.b.built[owner]
        got = hf.derive(self.m, rel_link(self.file, src_file), src_model, [target], owner)
        self.derived.update(got)
        return got[target]

    def fill_definition_refs(self) -> None:
        defs = {d["GUID"]: d for d in self.m["externalDefinitions"]["properties"]}
        for d in defs.values():
            d["definitionRefs"] = []

        def walk(entity_guid, a, path):
            if a.get("refType") == "external" and a.get("ref") in defs:
                defs[a["ref"]]["definitionRefs"].append([entity_guid, *path, a["GUID"]])
            for child in a.get("properties", []) or []:
                walk(entity_guid, child, [*path, a["GUID"]])

        for c in self.m["collections"]:
            for a in c.get("properties", []):
                walk(c["GUID"], a, [])

    def build(self) -> dict:
        for ecfg in self.cfg["entities"]:
            self.build_entity(ecfg)
        self.resolve()
        self.fill_definition_refs()
        return hf.finish(self.m)


# =========================================================================== the whole build

class Build:
    def __init__(self, linkml_src: Path, cfg: dict):
        self.schema = Schema(linkml_src)
        self.mapping = cfg["mapping"]
        self.specs = Specs(self.schema, self.mapping)
        self.cfg = cfg
        self.built: dict[str, tuple[dict, str]] = {}   # model name -> (json, repo-relative file)
        self.owner: dict[str, str] = {}                # entity name -> model name
        self.fk_targets: dict[tuple, tuple] = {}       # (model, entity, attr) -> (target, target attr)

    def run(self) -> dict[str, dict]:
        for mcfg in self.cfg["models"]:
            model = ModelBuilder(self, mcfg).build()
            self.built[mcfg["name"]] = (model, mcfg["file"])
        return {f: m for m, f in self.built.values()}


# The LinkML schemas live in the earlier repository, AvinashBhura/enterprise-data-model
# (D13). It is looked for here, in this order: --linkml-repo, the environment
# variable EDM_LINKML_REPO, then a clone named enterprise-data-model next to this one.
LINKML_REPO_NAME = "enterprise-data-model"


def find_linkml_repo(explicit: Path | None, tag: str) -> Path:
    candidates = [explicit, Path(os.environ["EDM_LINKML_REPO"]) if os.environ.get("EDM_LINKML_REPO") else None,
                  REPO.parent / LINKML_REPO_NAME, REPO]
    for c in candidates:
        if c is None:
            continue
        ok = subprocess.run(["git", "-C", str(c), "rev-parse", "--verify", "--quiet", f"refs/tags/{tag}"],
                            capture_output=True).returncode == 0
        if ok:
            return c
    raise SystemExit(
        f"Tag {tag} not found. Clone https://github.com/AvinashBhura/{LINKML_REPO_NAME} (with its tags) "
        f"next to this repository, or pass --linkml-repo PATH, or --linkml-src DIR with an extracted src/ folder.")


def linkml_from_tag(tag: str, repo: Path | None = None) -> Path:
    source = find_linkml_repo(repo, tag)
    tmp = Path(tempfile.mkdtemp(prefix="edm-linkml-"))
    archive = tmp / "src.tar"
    subprocess.run(["git", "-C", str(source), "archive", "--format=tar", "-o", str(archive), tag, "src"],
                   check=True)
    with tarfile.open(archive) as tar:
        tar.extractall(tmp, filter="data") if sys.version_info >= (3, 12) else tar.extractall(tmp)
    return tmp / "src"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--linkml-src", type=Path, help="extracted LinkML src/ folder (default: read from the tag)")
    ap.add_argument("--linkml-repo", type=Path, help="clone of the LinkML repository holding the tag (D13)")
    ap.add_argument("--out", type=Path, default=REPO, help="repository root to write into (default: this repository)")
    args = ap.parse_args(argv)
    cfg = yaml.safe_load((HERE / "models.yaml").read_text(encoding="utf-8"))
    src = args.linkml_src or linkml_from_tag(cfg["linkml_tag"], args.linkml_repo)
    build = Build(src, cfg)
    files = build.run()
    import physical  # noqa: E402  (needs the built polyglot models)
    files.update(physical.build(build))
    existing = [f for f in files if (args.out / f).exists()]
    if existing:
        print("Refusing to overwrite existing model files (spec 0002, requirement 6):")
        for f in existing:
            print("  ", f)
        print("Build into another folder with --out to compare.")
        return 1
    for f, m in files.items():
        hf.write(m, args.out / f)
        print("wrote", f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
