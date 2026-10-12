"""The EDM governance checks. Spec: specs/0001-repository-and-governance-checks/spec.md

Each check takes a Context and returns a list of Violations. Checks only read.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from .model import DEFINED, DERIVED, Attribute, Entity, Model, norm_name
from .report import Violation
from .rules import Rules


@dataclass
class Context:
    repo: Path
    rules: Rules
    models: list[Model]

    def rel(self, path: Path) -> str | None:
        try:
            return path.resolve().relative_to(self.repo.resolve()).as_posix()
        except ValueError:
            return None

    def readable(self) -> list[Model]:
        return [m for m in self.models if not m.errors]


def _ws(text) -> str:
    return " ".join(str(text or "").split())


# --------------------------------------------------------------------------- layers

def check_layers(ctx: Context) -> list[Violation]:
    """A model depends only on models in its own or a lower layer."""
    out = []
    for m in ctx.readable():
        if m.layer is None:
            out.append(Violation("layers", m.rel, "", "layers", "model file is not inside any layer folder"))
            continue
        for kind, link in m.dependencies():
            target = m.resolve(link)
            if target is None:
                continue  # remote reference: another repository, not checked here
            if not target.exists():
                out.append(Violation("layers", m.rel, link, "layers",
                                     f"{kind} link points to a file that does not exist"))
                continue
            rel = ctx.rel(target)
            if rel is None:
                out.append(Violation("layers", m.rel, link, "layers",
                                     f"{kind} link points outside the repository"))
                continue
            layer, rank = ctx.rules.layer_for(rel)
            if layer is None:
                out.append(Violation("layers", m.rel, link, "layers",
                                     f"{kind} link points to {rel}, which is not inside any layer folder"))
            elif rank > m.rank:
                out.append(Violation("layers", m.rel, link, "layers",
                                     f"{m.layer} model depends on {layer} model {rel} (dependencies must point to the same or a lower layer)"))
    return out


# --------------------------------------------------------------------------- cycles

def check_cycles(ctx: Context) -> list[Violation]:
    """No cycle in the dependency graph between model files."""
    graph: dict[str, set[str]] = defaultdict(set)
    for m in ctx.readable():
        for _, link in m.dependencies():
            target = m.resolve(link)
            if target is not None and target.exists():
                rel = ctx.rel(target)
                if rel:
                    graph[m.rel].add(rel)
    out, seen_cycles = [], set()
    state: dict[str, int] = {}  # 1 = on stack, 2 = done
    stack: list[str] = []

    def visit(node: str):
        state[node] = 1
        stack.append(node)
        for nxt in sorted(graph.get(node, ())):
            if state.get(nxt) == 1:
                cycle = stack[stack.index(nxt):]
                start = cycle.index(min(cycle))
                canon = tuple(cycle[start:] + cycle[:start])
                if canon not in seen_cycles:
                    seen_cycles.add(canon)
                    out.append(Violation("cycles", canon[0], "", "no-cycles",
                                         "dependency cycle: " + " -> ".join(canon + (canon[0],))))
            elif state.get(nxt) is None:
                visit(nxt)
        stack.pop()
        state[node] = 2

    for node in sorted(graph):
        if node not in state:
            visit(node)
    return out


# --------------------------------------------------------------------------- naming

def check_naming(ctx: Context) -> list[Violation]:
    """Business and technical names follow the configured rules."""
    import re
    cfg = ctx.rules.section("naming")
    ent_re = re.compile(cfg.get("entity_business_name", ".*"))
    att_re = re.compile(cfg.get("attribute_business_name", ".*"))
    tech_re = re.compile(cfg.get("technical_name", ".*"))
    max_len = int(cfg.get("max_technical_length", 63))
    reserved = {w.lower() for w in cfg.get("reserved_words", [])}
    out = []

    def tech(m, obj, code):
        if not code:
            return
        if not tech_re.fullmatch(code):
            out.append(Violation("naming", m.rel, obj, "naming.technical_name", f"technical name '{code}' does not match the pattern"))
        if len(code) > max_len:
            out.append(Violation("naming", m.rel, obj, "naming.max_technical_length", f"technical name '{code}' is longer than {max_len} characters"))
        if code.lower() in reserved:
            out.append(Violation("naming", m.rel, obj, "naming.reserved_words", f"technical name '{code}' is a reserved word"))

    for m in ctx.readable():
        owned = [e for e in m.entities() if e.kind == DEFINED] + m.model_definitions()
        for e in owned:
            if not ent_re.fullmatch(e.name):
                out.append(Violation("naming", m.rel, e.name, "naming.entity_business_name", f"entity name '{e.name}' does not match the pattern"))
            tech(m, e.name, e.data.get("code"))
            for a in e.all_attributes():
                if not att_re.fullmatch(a.name):
                    out.append(Violation("naming", m.rel, a.path, "naming.attribute_business_name", f"attribute name '{a.name}' does not match the pattern"))
                if a.name.lower() in reserved:
                    out.append(Violation("naming", m.rel, a.path, "naming.reserved_words", f"attribute name '{a.name}' is a reserved word"))
                tech(m, a.path, a.data.get("code"))
    return out


# --------------------------------------------------------------------------- metadata

def check_metadata(ctx: Context) -> list[Violation]:
    """Required custom properties are present and hold allowed values."""
    cfg = ctx.rules.section("metadata")
    allowed = cfg.get("allowed_values", {})
    out = []
    for m in ctx.readable():
        for prop in cfg.get("required_model_properties", []):
            value = m.data.get(prop)
            if not value:
                out.append(Violation("metadata", m.rel, "(model)", f"metadata.{prop}", f"model property '{prop}' is missing"))
            elif prop in allowed and value not in allowed[prop]:
                out.append(Violation("metadata", m.rel, "(model)", f"metadata.{prop}", f"'{prop}' = '{value}' is not one of {allowed[prop]}"))
        if m.data.get("edmLayer") and m.layer and m.data["edmLayer"] != m.layer:
            out.append(Violation("metadata", m.rel, "(model)", "metadata.edmLayer",
                                 f"edmLayer is '{m.data['edmLayer']}' but the file is in the {m.layer} layer folder"))
        for e in m.entities():
            if e.kind != DEFINED:
                continue
            for prop in cfg.get("required_entity_properties", []):
                value = e.data.get(prop)
                if not value:
                    out.append(Violation("metadata", m.rel, e.name, f"metadata.{prop}", f"entity property '{prop}' is missing"))
                elif prop in allowed and value not in allowed[prop]:
                    out.append(Violation("metadata", m.rel, e.name, f"metadata.{prop}", f"'{prop}' = '{value}' is not one of {allowed[prop]}"))
            if e.data.get("layer") and m.layer and e.data["layer"] != m.layer:
                out.append(Violation("metadata", m.rel, e.name, "metadata.layer",
                                     f"layer is '{e.data['layer']}' but the model is in the {m.layer} layer folder"))
            if cfg.get("require_entity_description", True) and not _ws(e.data.get("description")):
                out.append(Violation("metadata", m.rel, e.name, "metadata.description", "entity has no description"))
    return out


# --------------------------------------------------------------------------- foundation kind

def check_foundation_kind(ctx: Context) -> list[Violation]:
    """Strict-Foundation rule: every Domain, Process and Application entity specialises one Foundation kind."""
    cfg = ctx.rules.section("foundation")
    kinds = set(cfg.get("kinds", []))
    common_value = cfg.get("common_value", "none")
    specialising = set(cfg.get("specialising_layers", []))
    technical = [p.rstrip("/") + "/" for p in cfg.get("technical_paths", [])]
    out = []
    for m in ctx.readable():
        is_technical = any(m.rel.startswith(p) for p in technical)
        for e in m.entities():
            if e.kind != DEFINED:
                continue
            fk = e.foundation_kind
            if not fk:
                continue  # missing value is reported by check_metadata
            if is_technical and fk == common_value:
                continue  # technical construct shared by applications (foundation.technical_paths)
            if m.layer in specialising:
                if fk not in kinds:
                    out.append(Violation("foundation_kind", m.rel, e.name, "foundation.kinds",
                                         f"foundationKind '{fk}' is not exactly one Foundation kind ({', '.join(sorted(kinds))})"))
            elif m.layer == "Foundation":
                if fk != e.name:
                    out.append(Violation("foundation_kind", m.rel, e.name, "foundation.kinds",
                                         f"a Foundation entity's foundationKind must be its own name; found '{fk}'"))
            elif m.layer == "Common" and fk != common_value:
                out.append(Violation("foundation_kind", m.rel, e.name, "foundation.common_value",
                                     f"a Common entity's foundationKind must be '{common_value}'; found '{fk}'"))
    return out


# --------------------------------------------------------------------------- base types

def _items(attr: dict) -> list[dict]:
    """The item definitions of an array (Hackolade stores them under `properties`)."""
    items = attr.get("items", attr.get("properties"))
    if isinstance(items, dict):
        return [items]
    return [i for i in items or [] if isinstance(i, dict)]


def type_matches(attr: dict, type_word: str, type_map: dict) -> bool:
    """Does a Hackolade attribute match a contract type word? "a|b" means either."""
    type_word = type_word.strip()
    if "|" in type_word and not type_word.startswith("array<"):
        return any(type_matches(attr, t, type_map) for t in type_word.split("|"))
    if type_word.startswith("array<") and type_word.endswith(">"):
        if attr.get("type") != "array":
            return False
        inner = type_word[6:-1]
        return any(type_matches(i, inner, type_map) for i in _items(attr))
    if type_word.startswith("ref:"):
        target = type_word[4:]
        ref = str(attr.get("$ref", ""))
        return attr.get("type") == "reference" and (ref.endswith("/" + target) or ref == target)
    spec = type_map.get(type_word)
    if spec is None:
        return False
    if attr.get("type") != spec.get("type"):
        return False
    child = spec.get("childType")
    if child and attr.get("childType") is not None:
        allowed = child if isinstance(child, list) else [child]
        return attr["childType"] in allowed
    return True


def check_base_types(ctx: Context) -> list[Violation]:
    """Entities carry the attributes of every base type they list in edmComposes, as the contract says."""
    contracts = ctx.rules.section("base_types")
    type_map = ctx.rules.section("type_map")
    out = []
    for m in ctx.readable():
        for e in m.entities():
            if e.kind != DEFINED:
                continue
            raw = e.data.get("edmComposes") or ""
            if isinstance(raw, list):  # a multiple-select custom property stores a list
                raw = ";".join(map(str, raw))
            composes = [c.strip() for c in str(raw).replace(",", ";").split(";") if c.strip()]
            attrs = {a.name: a for a in e.attributes()}
            for c in composes:
                contract = contracts.get(c)
                if contract is None:
                    out.append(Violation("base_types", m.rel, e.name, "base_types", f"edmComposes names unknown base type '{c}'"))
                    continue
                for name, spec in (contract.get("attributes") or {}).items():
                    obj = f"{e.name}.{name}"
                    a = attrs.get(name)
                    if a is None:
                        out.append(Violation("base_types", m.rel, obj, f"base_types.{c}", "attribute required by the contract is missing"))
                        continue
                    if not type_matches(a.data, spec["type"], type_map):
                        out.append(Violation("base_types", m.rel, obj, f"base_types.{c}",
                                             f"type does not match contract type '{spec['type']}'"))
                    if bool(a.data.get("required")) != bool(spec.get("required")):
                        out.append(Violation("base_types", m.rel, obj, f"base_types.{c}",
                                             f"required is {bool(a.data.get('required'))}; the contract says {bool(spec.get('required'))}"))
                    if spec.get("primary_key") and not a.data.get("primaryKey"):
                        out.append(Violation("base_types", m.rel, obj, f"base_types.{c}", "must be the primary key"))
                    if spec.get("description") and _ws(a.description) != _ws(spec["description"]):
                        out.append(Violation("base_types", m.rel, obj, f"base_types.{c}",
                                             "description differs from the contract text"))
    return out


# --------------------------------------------------------------------------- enums

def check_enums(ctx: Context) -> list[Violation]:
    """The same attribute name carries the same enum values everywhere, unless allowed to differ."""
    cfg = ctx.rules.section("enums")
    skip = set(cfg.get("per_entity_attributes", [])) | set(cfg.get("intended_differences", []))
    seen: dict[str, list[tuple[frozenset, str, str]]] = defaultdict(list)
    for m in ctx.readable():
        owned = [e for e in m.entities() if e.kind == DEFINED] + m.model_definitions()
        for e in owned:
            for a in e.all_attributes():
                values = a.data.get("enum")
                if isinstance(values, list) and a.name not in skip:
                    seen[a.name].append((frozenset(map(str, values)), m.rel, a.path))
    out = []
    for name, uses in sorted(seen.items()):
        variants = {u[0] for u in uses}
        if len(variants) > 1:
            first = uses[0]
            for values, rel, path in uses[1:]:
                if values != first[0]:
                    extra = sorted(values - first[0])
                    missing = sorted(first[0] - values)
                    out.append(Violation("enums", rel, path, "enums",
                                         f"'{name}' enum differs from {first[2]} in {first[1]} (extra: {extra}; missing: {missing})"))
    return out


# --------------------------------------------------------------------------- junctions

def check_junctions(ctx: Context) -> list[Violation]:
    """A Bridge/Junction entity names the two entities it connects (edmConnects), has
    a relationship to each, and has its own key."""
    out = []
    for m in ctx.readable():
        rels = m.relationships()
        names = {c.guid: c.name for c in m.entities()}
        for e in m.entities():
            if e.kind != DEFINED or e.data.get("entityType") != "Bridge/Junction":
                continue
            connects = e.data.get("edmConnects") or []
            if isinstance(connects, str):
                connects = [c.strip() for c in connects.replace(",", ";").split(";") if c.strip()]
            parents = {norm_name(names.get(r.get("parentCollection"), "")) for r in rels
                       if r.get("childCollection") == e.guid}
            if len(connects) != 2:
                out.append(Violation("junctions", m.rel, e.name, "junctions",
                                     f"edmConnects must name the 2 entities the junction connects; found {len(connects)}"))
            for c in connects:
                if norm_name(c) not in parents:
                    out.append(Violation("junctions", m.rel, e.name, "junctions",
                                         f"no relationship to '{c}', which edmConnects names"))
            has_key = any(a.data.get("primaryKey") for a in e.attributes()) or bool(e.data.get("primaryKey"))
            if not has_key:
                out.append(Violation("junctions", m.rel, e.name, "junctions", "a junction needs its own primary key"))
    return out


# --------------------------------------------------------------------------- polymorphic references

def check_references(ctx: Context) -> list[Violation]:
    """Polymorphic reference pairs name entity types that exist in the EDM."""
    rules = ctx.rules.raw.get("polymorphic_references") or []
    subkinds = {norm_name(k): [norm_name(x) for x in v]
                for k, v in (ctx.rules.section("foundation").get("subkinds") or {}).items()}
    known: dict[str, str] = {}
    direct: dict[str, list[tuple[Model, Entity]]] = defaultdict(list)    # rule entity = the entity
    by_kind: dict[str, list[tuple[Model, Entity]]] = defaultdict(list)   # rule entity = its Foundation kind
    for m in ctx.readable():
        for e in [e for e in m.entities() if e.kind == DEFINED] + m.model_definitions():
            known[norm_name(e.name)] = e.name
            direct[norm_name(e.name)].append((m, e))
            kinds = set()
            if e.foundation_kind and e.foundation_kind != "none":
                kinds.add(norm_name(e.foundation_kind))
            kinds |= {parent for parent, subs in subkinds.items() if ({norm_name(e.name)} | kinds) & set(subs)}
            kinds.discard(norm_name(e.name))
            for k in kinds:   # a rule on a kind applies to the entities that carry its attributes (D12)
                by_kind[k].append((m, e))
    out = []
    covered = set()
    for rule in rules:
        owner_key = norm_name(rule["entity"])
        type_attr = rule["type_attribute"]
        targets = [(m, e, True) for m, e in direct.get(owner_key, [])]
        targets += [(m, e, False) for m, e in by_kind.get(owner_key, [])
                    if any(a.name == type_attr for a in e.all_attributes())]
        if not targets:
            continue  # the owning entity is not modelled yet
        allowed = {norm_name(n): n for n in rule.get("allowed", [])}
        id_attr = rule.get("id_attribute") or (type_attr[: -len("_type")] + "_id" if type_attr.endswith("_type") else None)
        m0, e0, _ = targets[0]
        for name in allowed.values():
            if norm_name(name) not in known:
                out.append(Violation("references", m0.rel, f"{rule['entity']}.{type_attr}", "polymorphic_references",
                                     f"allowed type '{name}' is not an entity in the EDM"))
        for m, e, is_direct in targets:
            covered.add((m.rel, e.guid, type_attr))
            attrs = [a for a in e.all_attributes() if a.name == type_attr]
            if not attrs and is_direct:
                out.append(Violation("references", m.rel, f"{e.name}.{type_attr}", "polymorphic_references",
                                     "configured type attribute is missing from the entity"))
            for a in attrs:
                values = a.data.get("enum")
                if isinstance(values, list):
                    bad = [v for v in values if norm_name(str(v)) not in allowed]
                    if bad:
                        out.append(Violation("references", m.rel, a.path, "polymorphic_references",
                                             f"enum values {bad} are not allowed types for this reference"))
                if id_attr and not any(x.name == id_attr for x in e.all_attributes()):
                    out.append(Violation("references", m.rel, a.path, "polymorphic_references",
                                         f"type attribute has no matching id attribute '{id_attr}'"))
    # every *_entity_type attribute must be configured
    for m in ctx.readable():
        for e in [e for e in m.entities() if e.kind == DEFINED] + m.model_definitions():
            for a in e.all_attributes():
                if a.name.endswith("_entity_type") and (m.rel, e.guid, a.name) not in covered:
                    out.append(Violation("references", m.rel, a.path, "polymorphic_references",
                                         "polymorphic reference is not listed in config/edm-rules.yaml"))
    return out


# --------------------------------------------------------------------------- deviations

def check_deviations(ctx: Context) -> list[Violation]:
    """No local change to derived Foundation/Common entities; other deviations need a reason."""
    cfg = ctx.rules.section("deviations")
    forbidden = set(cfg.get("forbidden_from_layers", []))
    reason_key = cfg.get("reason_property", "deviationReason")
    ignored = set(cfg.get("ignored_keys", []))
    physical = set(cfg.get("physical_type_keys", []))

    def meaningful(diff) -> list[str]:
        """Keys in a referenceDiff that are real modelling changes."""
        found = []
        if isinstance(diff, dict):
            for k, v in diff.items():
                if k in ignored:
                    continue
                if k in ("properties", "items"):
                    for child in (v if isinstance(v, list) else [v]):
                        found += meaningful(child)
                elif v not in (None, "", [], {}):
                    found.append(k)
        return found

    out = []
    for m in ctx.readable():
        for e in m.entities():
            if e.kind != DERIVED:
                continue
            changes = meaningful(e.data.get("referenceDiff") or {})
            if not changes:
                continue
            link = m.source_of_derived(e)
            source_layer = None
            if link:
                target = m.resolve(link)
                rel = ctx.rel(target) if target else None
                if rel:
                    source_layer, _ = ctx.rules.layer_for(rel)
            kinds = ", ".join(sorted(set(changes)))
            physical_only = not m.is_polyglot and set(changes) <= physical
            if source_layer in forbidden and not physical_only:
                out.append(Violation("deviations", m.rel, e.name, "deviations.forbidden_from_layers",
                                     f"entity derived from the {source_layer} layer has local changes ({kinds}); change it at its source instead"))
            elif not _ws(e.data.get(reason_key)):
                out.append(Violation("deviations", m.rel, e.name, "deviations.reason_property",
                                     f"local changes ({kinds}) need a reason in '{reason_key}'"))
    return out


# --------------------------------------------------------------------------- format

def _version(text: str) -> tuple[int, ...]:
    parts = []
    for p in str(text).split("."):
        digits = "".join(ch for ch in p if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def check_format(ctx: Context) -> list[Violation]:
    """Model files use a supported persistence schema and a recent enough Studio version."""
    cfg = ctx.rules.section("format")
    versions = [str(v) for v in cfg.get("persistence_schema_versions", [])]
    minimum = cfg.get("min_studio_version")
    out = []
    for m in ctx.models:
        for err in m.errors:
            out.append(Violation("format", m.rel, "", "format", err))
        if m.errors:
            continue
        psv = str(m.data.get("persistenceSchemaVersion", ""))
        if versions and psv not in versions:
            out.append(Violation("format", m.rel, "", "format.persistence_schema_versions",
                                 f"persistence schema version '{psv}' is not supported ({versions})"))
        saved_by = (m.data.get("applicationInformation") or {}).get("version")
        if cfg.get("accept_builder_output") and m.data.get("edmBuiltBy"):
            continue  # written by migration/build.py, awaiting Studio verification (D12)
        if minimum and (not saved_by or _version(saved_by) < _version(minimum)):
            out.append(Violation("format", m.rel, "", "format.min_studio_version",
                                 f"saved by Studio {saved_by or 'unknown'}; {minimum} or later is required"))
    return out


# --------------------------------------------------------------------------- ownership

def check_ownership(ctx: Context) -> list[Violation]:
    """Each entity is defined in exactly one model."""
    where: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for m in ctx.readable():
        for e in m.entities():
            if e.kind == DEFINED:
                where[norm_name(e.name)].append((m.rel, e.name))
    out = []
    for key, places in sorted(where.items()):
        files = sorted({p[0] for p in places})
        if len(places) > 1:
            for rel, name in places[1:]:
                out.append(Violation("ownership", rel, name, "single-owner",
                                     f"entity is also defined in {places[0][0]}; define it once and reference or derive it elsewhere"
                                     if len(files) > 1 else "entity is defined more than once in this model"))
    return out


# --------------------------------------------------------------------------- foundation contract

def _signature(attr: dict) -> tuple:
    """What must stay the same when an entity carries a Foundation attribute."""
    ref = str(attr.get("$ref", "")).rsplit("/", 1)[-1]
    children = tuple((c.get("name"), _signature(c)) for c in _items(attr)) \
        if attr.get("type") in ("array", "document") else ()
    values = tuple(attr["enum"]) if isinstance(attr.get("enum"), list) else ()
    return (attr.get("type"), attr.get("childType"), attr.get("mode"), attr.get("pattern"),
            values, ref, children)


def check_foundation_contract(ctx: Context) -> list[Violation]:
    """Every entity carries the attributes of its Foundation kind, as the Foundation
    model defines them (decision D12). Allowed changes: required may be tightened;
    listed enums may be narrowed, replaced, or closed from a string."""
    cfg = ctx.rules.section("foundation_contract")
    fcfg = ctx.rules.section("foundation")
    replaceable = set(cfg.get("replaceable_enums", []))
    narrowable = set(cfg.get("narrowable_enums", []))
    closable = set(cfg.get("string_to_enum", []))
    specialising = set(fcfg.get("specialising_layers", []))
    kinds: dict[str, Entity] = {}
    for m in ctx.readable():
        if m.layer == "Foundation":
            for e in m.entities():
                if e.kind == DEFINED:
                    kinds[e.name] = e
    supertype = {sub: sup for sup, subs in (fcfg.get("subkinds") or {}).items() for sub in subs}
    out = []
    for m in ctx.readable():
        for e in m.entities():
            if e.kind != DEFINED:
                continue
            if m.layer in specialising:
                kind_name = e.foundation_kind
            elif m.layer == "Foundation" and e.name in supertype:
                kind_name = supertype[e.name]       # LegalEntity carries Organization's attributes
            else:
                continue
            kind = kinds.get(kind_name)
            if kind is None:
                continue  # unknown kinds are reported by check_foundation_kind
            have = {a.name: a for a in e.attributes()}
            for fa in kind.attributes():
                obj = f"{e.name}.{fa.name}"
                a = have.get(fa.name)
                if a is None:
                    out.append(Violation("foundation_contract", m.rel, obj, "foundation_contract",
                                         f"attribute of Foundation {kind_name} is missing"))
                    continue
                f_sig, sig = _signature(fa.data), _signature(a.data)
                is_enum = a.data.get("childType") == "enum" and isinstance(a.data.get("enum"), list)
                if fa.name in replaceable:
                    ok = is_enum or sig == f_sig
                elif fa.name in narrowable:
                    f_values = set(fa.data.get("enum") or [])
                    ok = is_enum and bool(a.data["enum"]) and set(a.data["enum"]) <= f_values
                elif fa.name in closable and is_enum and fa.data.get("childType") != "enum":
                    ok = bool(a.data["enum"])
                else:
                    ok = sig == f_sig
                if not ok:
                    out.append(Violation("foundation_contract", m.rel, obj, "foundation_contract",
                                         f"differs from Foundation {kind_name}.{fa.name} in a way the rules do not allow"))
                if fa.data.get("required") and not a.data.get("required"):
                    out.append(Violation("foundation_contract", m.rel, obj, "foundation_contract",
                                         f"required in Foundation {kind_name}; may not be made optional"))
    return out


CHECKS = {
    "layers": check_layers,
    "cycles": check_cycles,
    "naming": check_naming,
    "metadata": check_metadata,
    "foundation_kind": check_foundation_kind,
    "base_types": check_base_types,
    "enums": check_enums,
    "junctions": check_junctions,
    "references": check_references,
    "deviations": check_deviations,
    "format": check_format,
    "ownership": check_ownership,
    "foundation_contract": check_foundation_contract,
}
