"""Write Hackolade model files (.hck.json) for the one-time builder (D5, D12).

Every structure here copies one seen in a file saved by Hackolade Studio
(persistence schema 8): the public sample models in hackolade/demo-models-read-only
(common/Address and common/Customer for external references, ecommerce/Order
management for polyglot derivation, Pragmatic data modeling/*-Oracle for derived
physical models, PostgreSQL/DVDrental for PostgreSQL columns, keys and indexes)
and the PostgreSQL plugin source (hackolade/PostgreSQL, types/).

GUIDs are UUID version 5 values built from names, so a rebuild writes identical
files. Standard library only.
"""

from __future__ import annotations

import copy
import json
import uuid
from pathlib import Path

NS = uuid.UUID("3b7d4c1e-5f0a-4e8b-9c2d-6a1f0e9b8c77")
TIMESTAMP = "2026-10-12T12:00:00.000Z"
# The newest Studio version among Hackolade's public sample models. Files are
# re-saved by Studio 8.13+ during verification, which updates this value.
APP_VERSION = "8.11.6"
COMPOSITE = ["compositePrimaryKey", "compositeUniqueKey"]
PG_COMPOSITE = ["compositePartitionKey", "compositePrimaryKey", "compositeUniqueKey"]
UUID_PATTERN = "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
FK_KEYS = ("relationshipType", "foreignCollection", "foreignField", "parentRelationship",
           "childRelationships")


def gid(*parts: str) -> str:
    return str(uuid.uuid5(NS, "/".join(str(p) for p in parts)))


# =========================================================================== attributes

def _attribute(guid: str, name: str | None, description: str, required: bool, pk: bool = False) -> dict:
    a = {"GUID": guid}
    if name is not None:
        a["name"] = name
    a.update({
        "isActivated": True,
        "primaryKey": pk,
        "required": required,
        "compositeKey": list(COMPOSITE),
        "compositePrimaryKey": False,
        "compositeUniqueKey": False,
        "error": {},
    })
    if description:
        a["description"] = description
    return a


def scalar(guid: str, name: str | None, kind: str, description: str = "", required: bool = False,
           pk: bool = False, pattern: str | None = None, values: list[str] | None = None,
           extra: dict | None = None) -> dict:
    """A Polyglot attribute of a simple type.

    kind: string, uuid, uri, date, datetime, time, decimal, integer, boolean, enum.
    A uuid is a string with the UUID pattern (the Polyglot target has no uuid
    type in any public sample; physical models change it to their uuid type).
    """
    a = _attribute(guid, name, description, required, pk)
    if kind in ("string", "uri"):
        a.update(type="string", childType="varchar")
        if kind == "uri":
            a["format"] = "uri"
    elif kind == "uuid":
        a.update(type="string", childType="varchar", pattern=UUID_PATTERN)
    elif kind == "date":
        a.update(type="string", childType="date")
    elif kind == "datetime":
        a.update(type="string", childType="timestamp_tz")
    elif kind == "time":
        a.update(type="string", childType="time")
    elif kind == "decimal":
        a.update(type="numeric", childType="number", mode="decimal",
                 exclusiveMinimum=False, exclusiveMaximum=False)
    elif kind == "integer":
        a.update(type="numeric", childType="integer", mode="int32",
                 exclusiveMinimum=False, exclusiveMaximum=False)
    elif kind == "boolean":
        a.update(type="boolean", childType="boolean")
    elif kind == "enum":
        a.update(type="string", childType="enum", enum=list(values or []))
    else:
        raise ValueError(f"unknown attribute kind {kind!r}")
    if pattern and kind != "uuid":
        a["pattern"] = pattern
    if extra:
        a.update(extra)
    return a


def obj(guid: str, name: str | None, properties: list[dict], description: str = "",
        required: bool = False) -> dict:
    a = _attribute(guid, name, description, required)
    a.update(type="document", childType="object", additionalProperties=False,
             properties=properties)
    return a


def array(guid: str, name: str, item: dict, description: str = "", required: bool = False) -> dict:
    """An array. Hackolade stores the item definitions under `properties`."""
    a = _attribute(guid, name, description, required)
    item = dict(item)
    item.pop("name", None)
    item["arrayItem"] = True
    a.update(type="array", childType="array", additionalItems=True, properties=[item])
    return a


def ext_ref(guid: str, name: str | None, model: dict, ext_def: dict, description: str = "",
            required: bool = False) -> dict:
    """An attribute that reuses an entity of another model (entity-level external
    reference, as common/Customer reuses common/Address)."""
    a = {
        "GUID": guid,
        "type": "reference",
        "$ref": f"#external/definitions/{ext_def['name']}",
        "refType": "external",
        "ref": ext_def["GUID"],
        "refIdPath": [model["GUID"], model["externalDefinitions"]["GUID"], ext_def["GUID"]],
        "isActivated": True,
        "compositeKey": list(COMPOSITE),
        "compositePrimaryKey": False,
        "compositeUniqueKey": False,
        "error": {"refPath": False},
    }
    if name is not None:
        a["name"] = name
        a["required"] = required
        a["primaryKey"] = False
        if description:
            a["refDescription"] = description
            a["error"]["refDescription"] = False
    else:
        a["displayName"] = ext_def["name"]
    return a


def describe(attr: dict) -> str:
    """The description of an attribute, wherever Hackolade keeps it."""
    return attr.get("description") or attr.get("refDescription") or ""


# =========================================================================== models

def new_model(name: str, description: str, target: str = "Polyglot", **custom) -> dict:
    m = {
        "modelName": name,
        "collections": [],
        "buckets": [],
        "views": [],
        "relationships": [],
        "users": [],
        "diagramViews": [],
        "idToNameHashTable": {},
        "definitions": {"type": "definitions", "properties": [], "GUID": gid(name, "definitions")},
        "polyglotDefinitions": {"type": "polyglotDefinitions", "properties": [],
                                "GUID": gid(name, "polyglotDefinitions")},
        "externalDefinitions": {"type": "externalDefinitions", "properties": [],
                                "GUID": gid(name, "externalDefinitions")},
        "sources": [],
        "decorativeSymbols": [],
        "businessGlossaries": [],
        "businessGlossaryTerms": [],
        "dbVendor": target,
        "appTarget": target,
        "creationTS": TIMESTAMP,
        "GUID": gid("model", name),
        "isLineageEnabled": False,
        "polyglotModelPaths": [],
        "lastModifTS": TIMESTAMP,
        "persistenceSchemaVersion": "8",
        "isCreatedByPlugin": True,
        "pluginInformation": {"pluginName": "Polyglot", "pluginVersion": "0.0.1",
                              "pluginEngineVersion": "1.0.0"},
        "applicationInformation": {"version": APP_VERSION},
        "hackoladeMeta": {"validationErrors": {}},
        "description": description,
        "settings": {},
        # Marks a file written by migration/build.py that Studio has not saved yet
        # (check_format, D12). Remove it when the file is verified in Studio.
        "edmBuiltBy": "migration/build.py",
    }
    m.update(custom)
    return m


def add_bucket(m: dict, name: str, description: str = "", color=(0, 188, 212)) -> dict:
    b = {
        "name": name,
        "type": "bucket",
        "collectionIds": [],
        "backgroundColor": {"r": color[0], "g": color[1], "b": color[2], "a": 1},
        "show": True,
        "isActivated": True,
        "GUID": gid(m["modelName"], "bucket", name),
        "hackoladeMeta": {"validationErrors": {}},
    }
    if description:
        b["description"] = description
    m["buckets"].append(b)
    return b


def add_entity(m: dict, bucket: dict, name: str, description: str, properties: list[dict],
               custom: dict) -> dict:
    c = {
        "GUID": gid(m["modelName"], "entity", name),
        "collectionName": name,
        "type": "object",
        "properties": properties,
        "definitions": {"type": "definitions", "properties": [],
                        "GUID": gid(m["modelName"], name, "definitions")},
        "isActivated": True,
        "additionalProperties": False,
        "bucketId": bucket["GUID"],
        "description": description,
        "hackoladeMeta": {"validationErrors": {}},
    }
    c.update({k: v for k, v in custom.items() if v not in (None, "", [])})
    m["collections"].append(c)
    bucket["collectionIds"].append(c["GUID"])
    return c


def add_unique_key(m: dict, entity: dict, attrs: list[dict], name: str) -> None:
    entity.setdefault("uniqueKey", []).append({
        "GUID": gid(m["modelName"], entity["collectionName"], "uk", name),
        "alternateKey": True,
        "constraintName": name,
        "compositeUniqueKey": [{"keyId": a["GUID"]} for a in attrs],
    })


def add_composite_pk(m: dict, entity: dict, attrs: list[dict], name: str) -> None:
    entity["primaryKey"] = [{
        "GUID": gid(m["modelName"], entity["collectionName"], "pk", name),
        "constraintName": name,
        "compositePrimaryKey": [{"keyId": a["GUID"]} for a in attrs],
    }]
    for a in attrs:
        a["compositePrimaryKey"] = True


def relate(m: dict, name: str, parent: dict, parent_attr_path: list[str], child: dict,
           child_attr: dict, required: bool = False, description: str = "") -> dict:
    """A foreign-key relationship. parent_attr_path is the parent field path as
    Hackolade stores it: [entityGUID, attrGUID] for a local entity, or
    [derivedEntityGUID, sourceEntityGUID, attrGUID] for a derived one."""
    r_guid = gid(m["modelName"], "relationship", child["GUID"], child_attr["GUID"])
    child_attr["relationshipType"] = "Foreign Key"
    child_attr["foreignCollection"] = parent["GUID"]
    child_attr["foreignField"] = list(parent_attr_path)
    child_attr["parentRelationship"] = r_guid
    r = {
        "name": name,
        "relationshipType": "Foreign Key",
        "parentField": [list(parent_attr_path)],
        "parentCardinality": "1",
        "childField": [[child["GUID"], child_attr["GUID"]]],
        "isActivated": True,
        "childCardinality": "0..n",
        "level": "field",
        "GUID": r_guid,
        "parentCollection": parent["GUID"],
        "childCollection": child["GUID"],
        "hackoladeMeta": {"validationErrors": {}},
    }
    if description:
        r["description"] = description
    m["relationships"].append(r)
    _note_child_relationship(m, parent, parent_attr_path[-1], r_guid)
    return r


def _note_child_relationship(m: dict, parent: dict, attr_guid: str, r_guid: str) -> None:
    if parent.get("refType") == "polyglot":
        diff = parent.setdefault("referenceDiff", {"properties": []})
        for p in diff["properties"]:
            if p["GUID"] == attr_guid:
                p.setdefault("childRelationships", []).append(r_guid)
                return
        diff["properties"].append({"GUID": attr_guid, "childRelationships": [r_guid]})
    else:
        for a in parent["properties"]:
            if a["GUID"] == attr_guid:
                a.setdefault("childRelationships", []).append(r_guid)


# =========================================================================== reuse across models

def _strip_custom_entity_keys(obj_: dict, keys) -> None:
    for k in keys:
        obj_.pop(k, None)


def external_definition(m: dict, link: str, source_model: dict, source_entity: dict,
                        entity_custom_keys=()) -> dict:
    """Copy an entity of another model into m.externalDefinitions, as Studio does
    for an entity-level external reference (sample: common/Customer -> Address)."""
    name = source_entity["collectionName"]
    for existing in m["externalDefinitions"]["properties"]:
        if existing["name"] == name and existing["link"] == link:
            return existing
    entry = copy.deepcopy(source_entity)
    _strip_custom_entity_keys(entry, ("bucketId", "definitions", "uniqueKey", "primaryKey",
                                      *entity_custom_keys))
    base = f"{m['modelName']}/ext/{name}"
    entry.update(
        type="document", childType="object", name=name, collectionName=name,
        compositeKey=list(COMPOSITE), compositePrimaryKey=False, compositeUniqueKey=False,
        GUID=gid(base), link=link, fieldRelativePath=f"#/{name}", kind="relativePath",
        fileType="hackoladeSchema", definitionRefs=[],
    )

    def regid(o: dict, path: str):
        for i, child in enumerate(o.get("properties", []) or []):
            child["GUID"] = gid(path, child.get("name") or f"item{i}")
            for k in FK_KEYS:
                child.pop(k, None)
            regid(child, f"{path}/{child.get('name') or i}")

    regid(entry, base)
    m["externalDefinitions"]["properties"].append(entry)
    return entry


def note_definition_ref(m: dict, ext_def: dict, entity: dict, attr_path: list[str]) -> None:
    ext_def["definitionRefs"].append([entity["GUID"], *attr_path])


def resolve_inline(source_model: dict, attrs: list[dict], models_by_link=None) -> list[dict]:
    """Copy attributes with every external reference replaced by the referenced
    object, keeping the attribute's GUID and description (as a polyglot
    derivation stores them: sample ecommerce/Order management, Customer copy)."""
    defs = {d["GUID"]: d for d in source_model["externalDefinitions"]["properties"]}

    def conv(a: dict) -> dict:
        if a.get("type") == "reference" and a.get("refType") == "external":
            target = defs[a["ref"]]
            out = {k: v for k, v in a.items() if k not in ("$ref", "refType", "ref", "refIdPath",
                                                           "refDescription", "displayName",
                                                           "error")}
            out.update(type="document", childType="object", additionalProperties=False,
                       properties=[conv(copy.deepcopy(p)) for p in target.get("properties", [])])
            if a.get("refDescription"):
                out["description"] = a["refDescription"]
            elif target.get("description") and not a.get("arrayItem"):
                out["description"] = target["description"]
            return out
        out = copy.deepcopy(a)
        if "properties" in out:
            out["properties"] = [conv(p) for p in out["properties"]]
        for k in FK_KEYS:
            out.pop(k, None)
        return out

    return [conv(a) for a in attrs]


def derive(m: dict, link: str, source_model: dict, entity_names: list[str],
           model_name_for_path: str) -> dict[str, dict]:
    """Derive entities from a parent polyglot model (polyglot derivation), as
    Studio stores it: polyglotModelPaths, read-only copies in polyglotDefinitions
    with the source GUIDs, a derived bucket and one derived collection per entity.
    Returns {name: derived collection}."""
    if not any(p["polyglotModelPath"] == link for p in m["polyglotModelPaths"]):
        m["polyglotModelPaths"].append({
            "GUID": gid(m["modelName"], "polyglotModelPath", link),
            "polyglotModelName": f"{model_name_for_path}.hck",
            "polyglotModelPath": link,
            "normalization": False,
            "applyTargetNamingConventions": True,
        })
    pd = m["polyglotDefinitions"]
    by_name = {c["collectionName"]: c for c in source_model["collections"]}
    buckets = {b["GUID"]: b for b in source_model["buckets"]}
    out = {}
    for name in entity_names:
        src = by_name[name]
        src_bucket = buckets[src["bucketId"]]
        # the derived bucket (one per source bucket)
        local_bucket = next((b for b in m["buckets"] if b.get("ref") == src_bucket["GUID"]), None)
        if local_bucket is None:
            bcopy = {k: v for k, v in src_bucket.items() if k != "collectionIds"}
            bcopy["collectionIds"] = []
            bcopy.update(definitionEntityType="bucket", fileType="hackoladeSchema",
                         definitionRefs=[], kind="relativePath", link=link,
                         fieldRelativePath=f"#/{src_bucket['name']}")
            pd["properties"].append(bcopy)
            local_bucket = {
                "GUID": gid(m["modelName"], "derivedBucket", link, src_bucket["name"]),
                "name": src_bucket["name"],
                "type": "reference",
                "$ref": f"#external/definitions/{src_bucket['name']}",
                "refType": "polyglot",
                "ref": src_bucket["GUID"],
                "refIdPath": [m["GUID"], pd["GUID"], src_bucket["GUID"]],
                "isActivated": True,
                "backgroundColor": src_bucket.get("backgroundColor"),
                "show": True,
                "collectionIds": [],
            }
            bcopy["definitionRefs"].append([local_bucket["GUID"]])
            bcopy["collectionIds"] = []
            m["buckets"].append(local_bucket)
        bcopy = next(p for p in pd["properties"]
                     if p.get("definitionEntityType") == "bucket" and p["GUID"] == src_bucket["GUID"])
        bcopy["collectionIds"].append(src["GUID"])

        ccopy = copy.deepcopy(src)
        ccopy["properties"] = resolve_inline(source_model, src["properties"])
        for k in ("uniqueKey", "primaryKey"):
            ccopy.pop(k, None)
        derived_guid = gid(m["modelName"], "derived", link, name)
        ccopy.update(definitionEntityType="collection", fileType="hackoladeSchema",
                     definitionRefs=[[derived_guid]], kind="relativePath", link=link,
                     fieldRelativePath=f"#/{src_bucket['name']}/{name}")
        pd["properties"].append(ccopy)
        c = {
            "GUID": derived_guid,
            "type": "reference",
            "$ref": f"#external/definitions/{name}",
            "refType": "polyglot",
            "ref": src["GUID"],
            "refIdPath": [m["GUID"], pd["GUID"], src["GUID"]],
            "isActivated": True,
            "collectionName": name,
            "bucketId": local_bucket["GUID"],
            "properties": [],
            "definitions": {"properties": [], "GUID": gid(m["modelName"], "derived", name, "definitions")},
            "additionalProperties": False,
            "error": {"refPath": False},
            "description": src.get("description", ""),
            "hackoladeMeta": {"validationErrors": {}},
        }
        m["collections"].append(c)
        local_bucket["collectionIds"].append(c["GUID"])
        out[name] = c
    return out


def source_attr(m: dict, derived: dict, attr_name: str) -> dict:
    """The copy (in polyglotDefinitions) of an attribute of a derived entity."""
    for p in m["polyglotDefinitions"]["properties"]:
        if p.get("definitionEntityType") == "collection" and p["GUID"] == derived["ref"]:
            for a in p["properties"]:
                if a.get("name") == attr_name:
                    return a
    raise KeyError(f"{derived['collectionName']}.{attr_name}")


# =========================================================================== finishing

def _hash_table(m: dict) -> dict:
    table = {}

    def walk(o):
        if isinstance(o, dict):
            label = o.get("collectionName") or o.get("name") or o.get("displayName")
            if "GUID" in o and label:
                table[o["GUID"]] = label
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(m["collections"])
    walk(m["buckets"])
    walk(m["relationships"])
    walk(m["polyglotDefinitions"]["properties"])
    return table


def finish(m: dict, columns: int = 4) -> dict:
    """Fill idToNameHashTable and a simple grid layout for the diagram."""
    m["idToNameHashTable"] = _hash_table(m)
    erd = []
    for i, c in enumerate(m["collections"]):
        erd.append({"GUID": c["GUID"], "x": 1000 + 420 * (i % columns),
                    "y": 1000 + 520 * (i // columns), "width": 360, "height": 460,
                    "color": {}})
    m["settings"] = {
        "centralPane": {
            "dbLevel": {
                "erd": erd,
                "erdDefinitions": {"erd": [], "rootPath": [], "entities": [], "decorativeSymbols": []},
                "buckets": [], "collapsedNodes": [], "activeRelationship": "",
                "activeRelationshipFields": {"childField": [], "parentField": []},
                "selectedCollections": [], "displayColorPicker": False,
                "graphView": {"erd": [], "buckets": [], "decorativeSymbols": [],
                              "forceLayout": True, "defaultLinkLength": 300},
                "diagramViews": [], "decorativeSymbols": [],
                "nestedCollectionsLayout": "horizontal", "options": [],
                "relationshipUpdateDisabled": False,
            },
            "collectionLevel": {},
            "changed": False,
        },
        "dtDiagram": {"collapsedNodes": [], "shouldDistributeCollections": False},
    }
    return m


def write(m: dict, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
