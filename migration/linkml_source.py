"""Read the frozen LinkML schemas (tag linkml-final-v0.5.0) for the one-time builder.

Only what the builder needs: classes with their parents, mixins, attributes and
slot_usage; enums with their values; and the induced attribute list of a class
(its own attributes plus those of its parents and mixins), in a stable order.

Standard library plus PyYAML. Read-only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

BUILTIN_TYPES = {"string", "integer", "decimal", "float", "double", "boolean", "date",
                 "datetime", "time", "uri", "uriorcurie", "uuid"}


@dataclass
class Slot:
    name: str
    range: str = "string"
    required: bool = False
    multivalued: bool = False
    identifier: bool = False
    description: str = ""
    pattern: str | None = None
    slot_uri: str | None = None
    minimum_value: float | None = None
    maximum_value: float | None = None
    owner: str = ""          # class that declared the attribute
    source_file: str = ""


@dataclass
class LinkClass:
    name: str
    description: str = ""
    is_a: str | None = None
    mixins: list[str] = field(default_factory=list)
    abstract: bool = False
    mixin: bool = False
    class_uri: str | None = None
    attributes: dict[str, Slot] = field(default_factory=dict)
    slot_usage: dict[str, dict] = field(default_factory=dict)
    file: str = ""


@dataclass
class LinkEnum:
    name: str
    description: str = ""
    values: dict[str, str] = field(default_factory=dict)   # value -> meaning
    file: str = ""


def _text(value) -> str:
    return " ".join(str(value or "").split())


def _slot(name: str, raw: dict | None, owner: str, file: str) -> Slot:
    raw = raw or {}
    return Slot(
        name=name,
        range=raw.get("range", "string"),
        required=bool(raw.get("required", False)),
        multivalued=bool(raw.get("multivalued", False)),
        identifier=bool(raw.get("identifier", False)),
        description=_text(raw.get("description")),
        pattern=raw.get("pattern"),
        slot_uri=raw.get("slot_uri"),
        minimum_value=raw.get("minimum_value"),
        maximum_value=raw.get("maximum_value"),
        owner=owner,
        source_file=file,
    )


class Schema:
    """Every class and enum found under a LinkML src/ folder."""

    def __init__(self, src: Path):
        self.src = Path(src)
        self.classes: dict[str, LinkClass] = {}
        self.enums: dict[str, LinkEnum] = {}
        self.types: dict[str, dict] = {}
        self.prefixes: dict[str, str] = {}
        for path in sorted(self.src.rglob("*.yaml")):
            rel = path.relative_to(self.src).as_posix()
            doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            for p, uri in (doc.get("prefixes") or {}).items():
                if isinstance(uri, str):
                    self.prefixes.setdefault(p, uri)
            for tname, t in (doc.get("types") or {}).items():
                self.types[tname] = t or {}
            for ename, e in (doc.get("enums") or {}).items():
                e = e or {}
                values = {}
                for v, meta in (e.get("permissible_values") or {}).items():
                    values[str(v)] = _text((meta or {}).get("description"))
                self.enums[ename] = LinkEnum(ename, _text(e.get("description")), values, rel)
            for cname, c in (doc.get("classes") or {}).items():
                c = c or {}
                cls = LinkClass(
                    name=cname,
                    description=_text(c.get("description")),
                    is_a=c.get("is_a"),
                    mixins=list(c.get("mixins") or []),
                    abstract=bool(c.get("abstract", False)),
                    mixin=bool(c.get("mixin", False)),
                    class_uri=c.get("class_uri"),
                    slot_usage=dict(c.get("slot_usage") or {}),
                    file=rel,
                )
                for aname, a in (c.get("attributes") or {}).items():
                    cls.attributes[aname] = _slot(aname, a, cname, rel)
                self.classes[cname] = cls

    # ------------------------------------------------------------------ helpers

    def expand_uri(self, curie: str | None) -> str:
        if not curie:
            return ""
        if "://" in curie:
            return curie
        prefix, _, local = curie.partition(":")
        base = self.prefixes.get(prefix)
        return f"{base}{local}" if base else curie

    def ancestors(self, name: str) -> list[str]:
        """is_a chain from the root down to the class itself."""
        chain = []
        while name:
            chain.append(name)
            name = self.classes[name].is_a
        return list(reversed(chain))

    def induced(self, name: str) -> dict[str, Slot]:
        """Attributes of a class: for each class in the is_a chain (root first),
        its own attributes, then those of its mixins; slot_usage applied last."""
        out: dict[str, Slot] = {}

        def add_class(cname: str):
            cls = self.classes[cname]
            for aname, slot in cls.attributes.items():
                out[aname] = _copy(slot) if aname not in out else _override(out[aname], slot)
            for mix in cls.mixins:
                for aname, slot in self.induced(mix).items():
                    if aname not in out:
                        out[aname] = _copy(slot)

        for cname in self.ancestors(name):
            add_class(cname)
            for aname, usage in (self.classes[cname].slot_usage or {}).items():
                if aname in out:
                    out[aname] = _apply_usage(out[aname], usage or {})
        return out


def _copy(slot: Slot) -> Slot:
    return Slot(**slot.__dict__)


def _override(base: Slot, new: Slot) -> Slot:
    return _copy(new)


def _apply_usage(slot: Slot, usage: dict) -> Slot:
    s = _copy(slot)
    if "range" in usage:
        s.range = usage["range"]
    if "required" in usage:
        s.required = bool(usage["required"])
    if "multivalued" in usage:
        s.multivalued = bool(usage["multivalued"])
    if usage.get("description"):
        s.description = _text(usage["description"])
    if "pattern" in usage:
        s.pattern = usage["pattern"]
    return s
