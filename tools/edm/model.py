"""Read Hackolade model files (.hck.json) for the EDM checks.

Read-only: nothing in tools/ ever writes a model file.

Terms used here:
- entity: a Hackolade collection (an entity in a polyglot model, a table in a physical one).
- defined entity: an entity the model owns (no $ref).
- derived entity: inherited from a parent polyglot model (refType "polyglot").
- referenced entity: reused from another model by external reference (refType "external").
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

DEFINED, DERIVED, REFERENCED = "defined", "derived", "referenced"


def norm_name(name: str) -> str:
    """Compare entity names loosely: 'Job Application' == 'JobApplication' == 'job_application'."""
    return "".join(ch for ch in name.lower() if ch.isalnum())


@dataclass
class Attribute:
    data: dict
    path: str  # e.g. "Person.natural_identifiers"

    @property
    def name(self) -> str:
        return self.data.get("name", "")

    @property
    def description(self) -> str:
        """Hackolade keeps a reference attribute's description in refDescription."""
        return self.data.get("description") or self.data.get("refDescription") or ""


@dataclass
class Entity:
    data: dict
    model: "Model"

    @property
    def name(self) -> str:
        return self.data.get("collectionName") or self.data.get("name", "")

    @property
    def guid(self) -> str:
        return self.data.get("GUID", "")

    @property
    def kind(self) -> str:
        ref_type = self.data.get("refType")
        if ref_type == "polyglot":
            return DERIVED
        if ref_type == "external" or "$ref" in self.data:
            return REFERENCED
        return DEFINED

    def attributes(self) -> list[Attribute]:
        """Top-level attributes only."""
        return [Attribute(a, f"{self.name}.{a.get('name', '?')}")
                for a in self.data.get("properties", []) if isinstance(a, dict)]

    @property
    def foundation_kind(self) -> str:
        return (self.data.get("foundationKind") or "").strip()

    def all_attributes(self) -> Iterator[Attribute]:
        """Every attribute, including those nested in objects and arrays.

        Hackolade stores the items of an array under `properties`, like the
        fields of an object; `items` is also read, for files from other tools."""
        def walk(items, prefix):
            if isinstance(items, dict):
                items = [items]
            for a in items or []:
                if not isinstance(a, dict):
                    continue
                path = f"{prefix}.{a['name']}" if a.get("name") else prefix
                if a.get("name"):
                    yield Attribute(a, path)
                yield from walk(a.get("properties"), path)
                yield from walk(a.get("items"), path)
        yield from walk(self.data.get("properties"), self.name)


@dataclass
class Model:
    path: Path               # absolute path of the .hck.json file
    rel: str                 # path relative to the repository root, with "/"
    data: dict
    layer: str | None = None
    rank: int | None = None
    errors: list[str] = field(default_factory=list)

    @property
    def name(self) -> str:
        return self.data.get("modelName", self.path.stem)

    @property
    def is_polyglot(self) -> bool:
        return self.data.get("dbVendor") == "Polyglot"

    def entities(self) -> list[Entity]:
        return [Entity(c, self) for c in self.data.get("collections", []) if isinstance(c, dict)]

    def model_definitions(self) -> list[Entity]:
        """Model-level definitions (reusable types), treated like defined entities."""
        props = (self.data.get("definitions") or {}).get("properties", [])
        return [Entity(d, self) for d in props if isinstance(d, dict)]

    def relationships(self) -> list[dict]:
        return [r for r in self.data.get("relationships", []) if isinstance(r, dict)]

    def dependencies(self) -> list[tuple[str, str]]:
        """(kind, link) for every other model this one depends on.

        kind is "derivation" (a parent polyglot model) or "reference" (an
        external definition). Links are as stored: usually relative paths.
        """
        deps = []
        for p in self.data.get("polyglotModelPaths", []) or []:
            if p.get("polyglotModelPath"):
                deps.append(("derivation", p["polyglotModelPath"]))
        for section in ("externalDefinitions", "polyglotDefinitions"):
            for d in (self.data.get(section) or {}).get("properties", []) or []:
                link = d.get("link")
                if isinstance(link, str) and link:
                    deps.append(("reference" if section == "externalDefinitions" else "derivation", link))
        seen, unique = set(), []
        for d in deps:
            if d not in seen:
                seen.add(d)
                unique.append(d)
        return unique

    def resolve(self, link: str) -> Path | None:
        """Resolve a stored link to a local file; None for remote links."""
        if "://" in link:
            return None
        return (self.path.parent / link).resolve()

    def source_of_derived(self, entity: Entity) -> str | None:
        """The link of the parent model an entity was derived from, if known."""
        ref = entity.data.get("ref")
        for section in ("polyglotDefinitions", "externalDefinitions"):
            for d in (self.data.get(section) or {}).get("properties", []) or []:
                if d.get("GUID") == ref and d.get("link"):
                    return d["link"]
        paths = [p.get("polyglotModelPath") for p in self.data.get("polyglotModelPaths", []) or []]
        return paths[0] if len(paths) == 1 else None


def load_models(repo: Path, rules) -> list[Model]:
    """Load every model file in scope, and assign each its layer."""
    models = []
    for root in rules.scope_roots:
        base = repo / root
        if not base.exists():
            continue
        for path in sorted(base.glob(rules.model_glob)):
            rel = path.relative_to(repo).as_posix()
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                m = Model(path.resolve(), rel, data)
            except (OSError, json.JSONDecodeError) as exc:
                m = Model(path.resolve(), rel, {}, errors=[f"cannot read model file: {exc}"])
            m.layer, m.rank = rules.layer_for(rel)
            models.append(m)
    return models
