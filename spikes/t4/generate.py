"""Generate the three spike T4 test models.

Writes small Hackolade polyglot models in the structure Hackolade Studio saves
(persistence schema 8), to test whether converter-written files open, save and
derive cleanly (spike T4) before the real converter is built (spec 0002, D5).

Standard library only. Deterministic: GUIDs are derived from names, so a re-run
produces identical files.

Usage:  python3 spikes/t4/generate.py            # writes into spikes/t4/generated/
"""

import json
import uuid
from pathlib import Path

OUT = Path(__file__).resolve().parent / "generated"
NS = uuid.UUID("6f1c0e52-8a5e-4c1e-9d0a-0e5c2b7a9e11")
TS = "2026-10-12T12:00:00.000Z"
APP_VERSION = "8.11.6"  # the newest Studio version among Hackolade's public sample models
COMPOSITE = ["compositePrimaryKey", "compositeUniqueKey"]


def gid(*parts):
    return str(uuid.uuid5(NS, "/".join(parts)))


# ---------------------------------------------------------------- attributes

def _base(model, entity, name, description, required, pk=False):
    return {
        "name": name,
        "hackoladeMeta": {},
        "isActivated": True,
        "primaryKey": pk,
        "required": required,
        "compositeKey": list(COMPOSITE),
        "GUID": gid(model, entity, name),
        "description": description,
        "error": {},
    }


def text(model, entity, name, description, required=False, pk=False, pattern=None):
    a = _base(model, entity, name, description, required, pk)
    a.update(type="string", childType="varchar")
    if pattern:
        a["pattern"] = pattern
    return a


def date(model, entity, name, description, required=False):
    a = _base(model, entity, name, description, required)
    a.update(type="string", childType="date")
    return a


def decimal(model, entity, name, description, required=False):
    a = _base(model, entity, name, description, required)
    a.update(type="numeric", childType="number", mode="decimal",
             exclusiveMinimum=False, exclusiveMaximum=False)
    return a


def enum(model, entity, name, description, values, required=False):
    a = _base(model, entity, name, description, required)
    a.update(type="string", childType="enum", enum=list(values))
    return a


def obj(model, entity, name, description, properties, required=False):
    a = _base(model, entity, name, description, required)
    a.update(type="document", childType="object", additionalProperties=False,
             properties=properties)
    return a


def ext_ref(referrer, ext_defs_guid, name, def_name, def_guid, description):
    """Attribute that points to an entry in the referrer's externalDefinitions."""
    return {
        "GUID": gid(referrer["GUID"], "ref", name),
        "name": name,
        "type": "reference",
        "$ref": f"#external/definitions/{def_name}",
        "refType": "external",
        "ref": def_guid,
        "refIdPath": [referrer["GUID"], ext_defs_guid, def_guid],
        "isActivated": True,
        "description": description,
        "hackoladeMeta": {},
    }


# ---------------------------------------------------------------- model shell

def model(name):
    m_guid = gid("model", name)
    return {
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
        "dbVendor": "Polyglot",
        "appTarget": "Polyglot",
        "creationTS": TS,
        "GUID": m_guid,
        "isLineageEnabled": False,
        "lastModifTS": TS,
        "persistenceSchemaVersion": "8",
        "isCreatedByPlugin": True,
        "pluginInformation": {"pluginName": "Polyglot", "pluginVersion": "0.0.1",
                              "pluginEngineVersion": "1.0.0"},
        "applicationInformation": {"version": APP_VERSION},
        "hackoladeMeta": {"validationErrors": {}},
        "description": "",
        "settings": {},
    }


def entity(m, name, description, properties, custom):
    c = {
        "GUID": gid(m["modelName"], "entity", name),
        "collectionName": name,
        "type": "object",
        "properties": properties,
        "definitions": {"type": "definitions", "properties": [],
                        "GUID": gid(m["modelName"], name, "definitions")},
        "isActivated": True,
        "additionalProperties": False,
        "bucketId": "",
        "description": description,
        "hackoladeMeta": {},
    }
    c.update(custom)  # EDM custom properties: does Studio keep them on save? (T4 step 3)
    m["collections"].append(c)
    return c


def relationship(m, name, parent, parent_field, child, child_field, child_card="0..n"):
    r_guid = gid(m["modelName"], "rel", name)
    child_field["parentRelationship"] = r_guid
    child_field["foreignCollection"] = parent["GUID"]
    child_field["foreignField"] = [parent["GUID"], parent_field["GUID"]]
    child_field["relationshipType"] = "Foreign Key"
    m["relationships"].append({
        "name": name,
        "relationshipType": "Foreign Key",
        "parentField": [[parent["GUID"], parent_field["GUID"]]],
        "parentCardinality": "1",
        "childField": [[child["GUID"], child_field["GUID"]]],
        "isActivated": True,
        "childCardinality": child_card,
        "level": "field",
        "GUID": r_guid,
        "parentCollection": parent["GUID"],
        "childCollection": child["GUID"],
        "hackoladeMeta": {"validationErrors": {}},
    })


def external_definition(referrer, source_path, field_path, source_obj, name):
    """Copy a definition from another model into the referrer, as Studio does."""
    entry = json.loads(json.dumps(source_obj))
    if "collectionName" in entry:  # an entity is copied as a document object
        for key in ("bucketId", "definitions", "layer", "foundationKind", "entityType",
                    "edmComposes"):
            entry.pop(key, None)
        entry.update(type="document", childType="object", compositeKey=list(COMPOSITE),
                     compositePrimaryKey=False, compositeUniqueKey=False)
    entry.update(name=name, link=source_path, fieldRelativePath=field_path,
                 kind="relativePath", fileType="hackoladeSchema", definitionRefs=[])
    entry["GUID"] = gid(referrer["modelName"], "ext", name)

    def regid(o, path):  # Studio gives every copied child a new GUID
        for child in o.get("properties", []):
            child["GUID"] = gid(path, child["name"])
            regid(child, f"{path}/{child['name']}")

    regid(entry, f"{referrer['modelName']}/ext/{name}")
    referrer["externalDefinitions"]["properties"].append(entry)
    return entry


def finish(m):
    """Fill idToNameHashTable and a simple diagram layout, then write the file."""
    table = {}

    def walk(o):
        if isinstance(o, dict):
            if "GUID" in o and ("name" in o or "collectionName" in o):
                table[o["GUID"]] = o.get("collectionName") or o.get("name")
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(m["collections"])
    m["idToNameHashTable"] = table
    erd = [{"GUID": c["GUID"], "x": 1000 + 360 * i, "y": 1000, "width": 300, "height": 200,
            "color": {"hex": "#2196F3"}} for i, c in enumerate(m["collections"])]
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
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{m['modelName']}.hck.json"
    path.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


# ---------------------------------------------------------------- the three models

def build():
    # 1. Common: one model definition, AmountType.
    common = model("EDM Spike Common")
    common["description"] = "Spike T4: shared value types, reused by external reference (D2)."
    amount = obj("EDM Spike Common", "definitions", "AmountType",
                 "A monetary amount: a decimal value with its ISO 4217 currency code.", [
                     decimal("EDM Spike Common", "AmountType", "value", "The numeric amount.", True),
                     text("EDM Spike Common", "AmountType", "currency",
                          "ISO 4217 three-letter currency code.", True, pattern="^[A-Z]{3}$"),
                 ])
    common["definitions"]["properties"].append(amount)
    finish(common)

    # 2. Foundation: Entity, Person, Role, Agreement.
    fm = "EDM Spike Foundation"
    found = model(fm)
    found["description"] = "Spike T1, T3, T4: a four-entity slice of the Foundation."

    def eid(e):
        return text(fm, e, "entity_id", "Globally unique surrogate identifier (UUID).", True, pk=True)

    entity(found, "Entity", "Root of the EDM. Polyglot only in the real model (spike T1).",
           [eid("Entity")], {"layer": "Foundation", "foundationKind": "Entity", "entityType": "Core"})
    person = entity(found, "Person", "A human being; not an employee or a customer.", [
        eid("Person"),
        text(fm, "Person", "given_name", "Given (first) name.", True),
        text(fm, "Person", "family_name", "Family (last) name.", True),
        date(fm, "Person", "date_of_birth", "Date of birth."),
        enum(fm, "Person", "lifecycle_state", "Entity-level lifecycle state.",
             ["PROSPECT", "ACTIVE", "INACTIVE", "MERGED", "ARCHIVED", "DECEASED"], True),
    ], {"layer": "Foundation", "foundationKind": "Person", "entityType": "Core",
        "edmComposes": "Identifiable;Lifecycleable"})
    held_by = text(fm, "Role", "held_by_person", "The Person who holds this role.")
    role = entity(found, "Role", "A time-bound engagement of a Person with another party.", [
        eid("Role"),
        enum(fm, "Role", "role_type", "Kind of role.", ["EMPLOYEE", "CONTRACTOR", "CANDIDATE"], True),
        held_by,
        date(fm, "Role", "effective_from", "When the role starts.", True),
    ], {"layer": "Foundation", "foundationKind": "Role", "entityType": "Core"})
    relationship(found, "holds", person, person["properties"][0], role, held_by)

    ext_amount = external_definition(found, "EDM Spike Common.hck.json", "#/definitions/AmountType",
                                     amount, "AmountType")
    entity(found, "Agreement", "A formal commitment between two or more parties.", [
        eid("Agreement"),
        text(fm, "Agreement", "title", "Agreement title.", True),
        ext_ref(found, found["externalDefinitions"]["GUID"], "total_value", "AmountType",
                ext_amount["GUID"], "Total value of the agreement (shared AmountType)."),
    ], {"layer": "Foundation", "foundationKind": "Agreement", "entityType": "Core"})
    finish(found)

    # 3. Referrer: reuses an entity (known-good pattern) and a model definition (unknown pattern).
    rm = "EDM Spike Referrer"
    ref = model(rm)
    ref["description"] = ("Spike T4: an entity-level reference (pattern seen in Hackolade's samples) "
                          "and a model-definition reference (pattern not seen in any public sample).")
    ext_person = external_definition(ref, "EDM Spike Foundation.hck.json", "#/Person", person, "Person")
    ext_amount2 = external_definition(ref, "EDM Spike Common.hck.json", "#/definitions/AmountType",
                                      amount, "AmountType")
    entity(ref, "Candidate Profile", "Test entity using two kinds of external reference.", [
        text(rm, "Candidate Profile", "profile_id", "Identifier.", True, pk=True),
        ext_ref(ref, ref["externalDefinitions"]["GUID"], "person", "Person", ext_person["GUID"],
                "The person (entity-level external reference)."),
        ext_ref(ref, ref["externalDefinitions"]["GUID"], "expected_salary", "AmountType",
                ext_amount2["GUID"], "Expected salary (model-definition external reference)."),
    ], {"layer": "Domain", "foundationKind": "Role", "entityType": "Core"})
    finish(ref)


if __name__ == "__main__":
    build()
    for p in sorted(OUT.glob("*.hck.json")):
        print("wrote", p.relative_to(OUT.parent.parent.parent))
