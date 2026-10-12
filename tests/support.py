"""Build small Hackolade-shaped model files in a temporary repository, for tests.

Only the keys the checks read are written. These fixtures test the checks; they
are not meant to be opened in Hackolade Studio.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

from edm.checks import CHECKS, Context  # noqa: E402
from edm.model import load_models  # noqa: E402
from edm.rules import Rules  # noqa: E402


def gid() -> str:
    return str(uuid.uuid4())


def attr(name, type_="string", child="varchar", required=False, pk=False, description="", **extra):
    a = {"name": name, "type": type_, "required": required, "primaryKey": pk,
         "description": description, "GUID": gid()}
    if child is not None:
        a["childType"] = child
    a.update(extra)
    return a


def enum_attr(name, values, required=False, description=""):
    return attr(name, "string", "enum", required, description=description, enum=list(values))


def ref_attr(name, target, description=""):
    return {"name": name, "type": "reference", "$ref": f"#model/definitions/{target}",
            "GUID": gid(), "description": description}


def array_of_ref(name, target, description=""):
    return {"name": name, "type": "array", "GUID": gid(), "required": False,
            "description": description, "items": [ref_attr("item", target)]}


class Repo:
    """A throwaway repository with the real rules file and a src/ tree."""

    def __init__(self):
        self.root = Path(tempfile.mkdtemp(prefix="edm-test-"))
        (self.root / "config").mkdir()
        shutil.copy(REPO / "config" / "edm-rules.yaml", self.root / "config" / "edm-rules.yaml")

    def cleanup(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def model(self, rel_path, layer=None, name=None, polyglot=True, version="8.13.0", **top):
        m = {
            "modelName": name or Path(rel_path).stem,
            "GUID": gid(),
            "dbVendor": "Polyglot" if polyglot else "PostgreSQL",
            "persistenceSchemaVersion": "8",
            "applicationInformation": {"version": version},
            "collections": [], "relationships": [],
            "definitions": {"type": "definitions", "properties": [], "GUID": gid()},
            "externalDefinitions": {"type": "externalDefinitions", "properties": [], "GUID": gid()},
            "polyglotDefinitions": {"type": "polyglotDefinitions", "properties": [], "GUID": gid()},
        }
        if layer:
            m["edmLayer"] = layer
        m.update(top)
        return Model(self, rel_path, m)

    def check(self, name):
        rules = Rules.load(self.root)
        ctx = Context(self.root, rules, load_models(self.root, rules))
        return CHECKS[name](ctx)


class Model:
    def __init__(self, repo, rel_path, data):
        self.repo, self.rel_path, self.data = repo, rel_path, data

    def entity(self, name, attrs=(), layer=None, foundation_kind=None, entity_type="Core",
               steward="EDM architecture", description="An entity.", **props):
        c = {"GUID": gid(), "collectionName": name, "type": "object",
             "properties": list(attrs), "description": description}
        meta = {"layer": layer or self.data.get("edmLayer"), "foundationKind": foundation_kind,
                "entityType": entity_type, "steward": steward}
        c.update({k: v for k, v in meta.items() if v is not None})
        c.update(props)
        self.data["collections"].append(c)
        return c

    def definition(self, name, attrs=()):
        d = {"GUID": gid(), "name": name, "type": "document", "childType": "object",
             "properties": list(attrs)}
        self.data["definitions"]["properties"].append(d)
        return d

    def derived(self, name, parent_link, reference_diff=None, **props):
        """An entity derived from a parent polyglot model."""
        entry = {"GUID": gid(), "name": name, "collectionName": name, "link": parent_link}
        self.data["polyglotDefinitions"]["properties"].append(entry)
        paths = self.data.setdefault("polyglotModelPaths", [])
        if not any(p["polyglotModelPath"] == parent_link for p in paths):
            paths.append({"GUID": gid(), "polyglotModelPath": parent_link})
        c = {"GUID": gid(), "collectionName": name, "type": "object", "refType": "polyglot",
             "$ref": f"#external/definitions/{name}", "ref": entry["GUID"]}
        if reference_diff is not None:
            c["referenceDiff"] = reference_diff
        c.update(props)
        self.data["collections"].append(c)
        return c

    def reference(self, name, link):
        """An external definition pointing to another model file."""
        e = {"GUID": gid(), "name": name, "link": link, "kind": "relativePath"}
        self.data["externalDefinitions"]["properties"].append(e)
        return e

    def relate(self, name, parent, child):
        self.data["relationships"].append({"name": name, "GUID": gid(), "relationshipType": "Foreign Key",
                                           "parentCollection": parent["GUID"],
                                           "childCollection": child["GUID"]})

    def save(self):
        path = self.repo.root / self.rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
        return path
