"""Write the Candidate Journey physical model for PostgreSQL (spec 0005, D8, D12).

The file has the structure of a model derived by Hackolade's polyglotDerive
(sample: Pragmatic data modeling/3-Referencing-Oracle): every table is a
derived entity that points to a read-only copy of its logical entity in
polyglotDefinitions, with data types converted to PostgreSQL (types from the
hackolade/PostgreSQL plugin and the PostgreSQL sample models). Physical design
choices are local: schema, keys, indexes and foreign keys, and the change of
uuid columns, which is a tracked deviation with a reason.

The physical design is also listed in
src/04_application/CandidateJourney/README.md, so it can be re-applied if
Studio's own derivation is preferred (D12).
"""

from __future__ import annotations

import copy

import hackolade_file as hf

FILE = "src/04_application/CandidateJourney/CandidateJourney-PostgreSQL.hck.json"
MODEL = "CandidateJourney"
SCHEMA = "candidate_journey"
PLUGIN = {"pluginName": "PostgreSQL", "pluginVersion": "0.2.53", "pluginEngineVersion": "1.0.0"}

# Parent polyglot model -> entities that become tables, in stage order (spec 0005, requirement 3)
TABLES = [
    ("TalentAcquisition", ["JobRequisition", "RequisitionPositionLink", "JobPosting",
                           "CandidateSourceChannel"]),
    ("Foundation", ["Person"]),
    ("TalentAcquisition", ["Candidate", "CandidateSourceAttribution", "EmployeeReferral",
                           "RecruitingAgency", "TalentPipeline",
                           "JobApplication", "Assessment",
                           "Interview", "InterviewPanelAssignment",
                           "SelectionDecision", "BackgroundCheck", "Offer"]),
    ("CoreProcess", ["ProcessDefinition", "ProcessStep", "ProcessTransition", "ProcessInstance",
                     "StepCompletion", "ProcessEvent"]),
    ("ApplicationShared", ["SourceSystemReference"]),
]
STAGES = {
    "Sourcing": ["JobRequisition", "RequisitionPositionLink", "JobPosting", "CandidateSourceChannel",
                 "Person", "Candidate", "CandidateSourceAttribution", "EmployeeReferral",
                 "RecruitingAgency", "TalentPipeline"],
    "Application and screening": ["JobApplication", "Assessment"],
    "Interviewing": ["Interview", "InterviewPanelAssignment"],
    "Selection": ["SelectionDecision", "BackgroundCheck", "Offer"],
    "Journey tracking": ["ProcessDefinition", "ProcessStep", "ProcessTransition", "ProcessInstance",
                         "StepCompletion", "ProcessEvent"],
    "Source of record": ["SourceSystemReference"],
}
# Extra indexes beyond foreign keys (spec 0005, requirement 8)
EXTRA_INDEXES = {
    "JobRequisition": [["lifecycle_state"]],
    "JobApplication": [["lifecycle_state"]],
    "ProcessInstance": [["lifecycle_state"], ["subject_entity_type", "subject_entity_id"]],
}
EXTRA_UNIQUE = {
    "SourceSystemReference": [["referenced_entity_type", "referenced_entity_id", "source_system"]],
}
UUID_REASON = ("entity_id and every reference to an entity_id use the PostgreSQL uuid type; "
               "the logical model stores them as text with the UUID pattern.")


def snake(name: str) -> str:
    out = ""
    for i, ch in enumerate(name):
        if ch.isupper() and i and (not name[i - 1].isupper() or (i + 1 < len(name) and name[i + 1].islower())):
            out += "_"
        out += ch.lower()
    return out


# =========================================================================== type conversion

def _json_child(a: dict) -> dict:
    """A field inside a jsonb column."""
    out = {k: v for k, v in a.items() if k in ("GUID", "name", "description", "required", "isActivated",
                                              "arrayItem", "displayName")}
    t = a.get("type")
    if t == "document":
        out.update(type="jsonObject", additionalProperties=False,
                   properties=[_json_child(c) for c in a.get("properties", [])])
    elif t == "array":
        out.update(type="jsonArray", properties=[_json_child(c) for c in a.get("properties", [])])
    elif t == "numeric":
        out["type"] = "jsonNumber"
    elif t == "boolean":
        out["type"] = "jsonBoolean"
    else:
        out["type"] = "jsonString"
    out.setdefault("isActivated", True)
    return out


def to_postgresql(a: dict) -> dict:
    """Convert one Polyglot attribute to its PostgreSQL column form."""
    out = {k: v for k, v in a.items() if k not in ("type", "childType", "mode", "compositeKey",
                                                   "format", "exclusiveMinimum", "exclusiveMaximum",
                                                   "additionalItems", "properties", "additionalProperties")}
    t, ct = a.get("type"), a.get("childType")
    if t == "string" and ct == "date":
        out.update(type="string", childType="datetime", mode="date")
    elif t == "string" and ct in ("timestamp_tz", "timestamp"):
        out.update(type="string", childType="datetime", mode="timestamp", timezone="WITH TIME ZONE")
    elif t == "string" and ct == "time":
        out.update(type="string", childType="datetime", mode="time")
    elif t == "string":                       # varchar, enum (kept as a CHECK list)
        out.update(type="string", childType="char", mode="varchar")
    elif t == "numeric" and ct == "integer":
        out.update(type="numeric", childType="numeric", mode="integer",
                   exclusiveMinimum=False, exclusiveMaximum=False)
    elif t == "numeric":
        out.update(type="numeric", childType="numeric", mode="numeric",
                   exclusiveMinimum=False, exclusiveMaximum=False)
    elif t == "boolean":
        out.update(type="boolean", childType="boolean")
    elif t == "document":
        out.update(type="jsonObject", childType="json", mode="jsonb", subtype="object",
                   additionalProperties=False,
                   properties=[_json_child(c) for c in a.get("properties", [])])
    elif t == "array":
        out.update(type="jsonArray", childType="json", mode="jsonb", subtype="array",
                   properties=[_json_child(c) for c in a.get("properties", [])])
    else:
        raise ValueError(f"{a.get('name')}: no PostgreSQL form for {t}/{ct}")
    out.update(compositeKey=list(hf.PG_COMPOSITE), compositePartitionKey=False,
               unique=False, code=a["name"], hackoladeMeta={"namingConvention": "code"})
    return out


def is_uuid(a: dict) -> bool:
    return a.get("type") == "string" and a.get("pattern") == hf.UUID_PATTERN


# =========================================================================== build

def build(b) -> dict[str, dict]:
    """b: the polyglot Build (migration/build.py), with every parent already built."""
    m = hf.new_model(MODEL, (
        "Candidate Journey application: the PostgreSQL physical model for sourcing, "
        "application and screening, interviewing and selection, up to the hand-over to "
        "hiring. Derived from TalentAcquisition, Foundation (Person), CoreProcess and "
        "ApplicationShared (greenfield workflow, docs/workflows/greenfield.md). Entities "
        "owned by other HR subdomains are referenced by entity_id only; their system-of-"
        "record keys are in source_system_reference."),
        target="PostgreSQL", edmLayer="Application", dbVersion="v16.x", code=SCHEMA,
        database_name=SCHEMA)
    m["pluginInformation"] = dict(PLUGIN)
    bucket = hf.add_bucket(m, SCHEMA, "All Candidate Journey tables.", color=(216, 0, 115))
    bucket.update(code=SCHEMA, ifNotExist=True)
    pd = m["polyglotDefinitions"]

    tables: dict[str, dict] = {}       # entity name -> local collection
    copies: dict[str, dict] = {}       # entity name -> copy in polyglotDefinitions
    sources: dict[str, tuple] = {}     # entity name -> (parent model name, source collection)
    for parent_name, names in TABLES:
        src_model, src_file = b.built[parent_name]
        link = hf_rel(FILE, src_file)
        if not any(p["polyglotModelPath"] == link for p in m["polyglotModelPaths"]):
            m["polyglotModelPaths"].append({
                "GUID": hf.gid(MODEL, "polyglotModelPath", link),
                "polyglotModelName": f"{parent_name}.hck",
                "polyglotModelPath": link,
                "normalization": False,
                "applyTargetNamingConventions": True,
            })
        src_buckets = {x["GUID"]: x for x in src_model["buckets"]}
        for name in names:
            src = next(c for c in src_model["collections"] if c["collectionName"] == name)
            local_guid = hf.gid(MODEL, "table", name)
            c_copy = copy.deepcopy(src)
            c_copy["properties"] = [to_postgresql(a) for a in hf.resolve_inline(src_model, src["properties"])]
            for k in ("uniqueKey", "primaryKey", "edmComposes", "edmConnects", "edmValueType",
                      "edmAbstract", "sourceTaxonomyRef"):
                c_copy.pop(k, None)
            c_copy.update(code=snake(name), hackoladeMeta={"validationErrors": {}, "namingConvention": "code"},
                          definitionEntityType="collection", link=link, kind="relativePath",
                          fieldRelativePath=f"#/{src_buckets[src['bucketId']]['name']}/{name}",
                          fileType="hackoladeSchema", definitionRefs=[[local_guid]])
            pd["properties"].append(c_copy)
            local = {
                "isActivated": True,
                "collectionName": name,
                "type": "reference",
                "properties": [],
                "definitions": {"properties": [], "GUID": hf.gid(MODEL, "table", name, "definitions")},
                "additionalProperties": False,
                "code": snake(name),
                "GUID": local_guid,
                "$ref": f"#external/definitions/{name}",
                "refType": "polyglot",
                "ref": src["GUID"],
                "refIdPath": [m["GUID"], pd["GUID"], src["GUID"]],
                "bucketId": bucket["GUID"],
                "ifNotExist": True,
                "hackoladeMeta": {"namingConvention": "code", "validationErrors": {}},
                "referenceDiff": {"properties": []},
            }
            m["collections"].append(local)
            bucket["collectionIds"].append(local_guid)
            tables[name], copies[name], sources[name] = local, c_copy, (parent_name, src)

    def diff(name: str, attr_guid: str) -> dict:
        props = tables[name]["referenceDiff"]["properties"]
        for p in props:
            if p["GUID"] == attr_guid:
                return p
        p = {"GUID": attr_guid}
        props.append(p)
        return p

    def column(name: str, col: str) -> dict:
        return next(a for a in copies[name]["properties"] if a["name"] == col)

    # ---- uuid columns (deviation)
    for name, c_copy in copies.items():
        changed = False
        for a in c_copy["properties"]:
            if a.get("pattern") == hf.UUID_PATTERN:
                diff(name, a["GUID"]).update(childType="uuid", mode="")
                changed = True
        if changed:
            tables[name]["deviationReason"] = UUID_REASON

    # ---- keys
    for name, local in tables.items():
        pk = next(a for a in copies[name]["properties"] if a.get("primaryKey"))
        local["primaryKey"] = [{"GUID": hf.gid(MODEL, name, "pk"), "constraintName": f"{snake(name)}_pkey",
                                "compositePrimaryKey": [{"keyId": pk["GUID"]}]}]
        _, src = sources[name]
        uniques = []
        for uk in src.get("uniqueKey", []) or []:
            uniques.append([k["keyId"] for k in uk["compositeUniqueKey"]])
        for cols in EXTRA_UNIQUE.get(name, []):
            uniques.append([column(name, c)["GUID"] for c in cols])
        local["uniqueKey"] = []
        for ids in uniques:
            cols = [next(a["name"] for a in copies[name]["properties"] if a["GUID"] == i) for i in ids]
            local["uniqueKey"].append({
                "GUID": hf.gid(MODEL, name, "uk", *cols),
                "constraintName": f"{snake(name)}_{'_'.join(cols)}_key",
                "compositeUniqueKey": [{"keyId": i} for i in ids],
            })

    # ---- foreign keys: only where both tables are in this model (spec 0005, requirement 5)
    indexes: dict[str, list[list[str]]] = {n: [] for n in tables}
    for name in tables:
        parent_model, _ = sources[name]
        for a in copies[name]["properties"]:
            target = b.fk_targets.get((parent_model, name, a["name"]))
            if not target:
                continue
            t_name, t_attr = target
            if t_name not in tables:
                continue
            p_attr = (column(t_name, t_attr) if t_attr
                      else next(x for x in copies[t_name]["properties"] if x.get("primaryKey")))
            r_guid = hf.gid(MODEL, "relationship", name, a["name"])
            parent_path = [tables[t_name]["GUID"], copies[t_name]["GUID"], p_attr["GUID"]]
            m["relationships"].append({
                "name": f"fk_{snake(name)}_{a['name']}",
                "relationshipType": "Foreign Key",
                "parentField": [parent_path],
                "parentCardinality": "1",
                "childField": [[tables[name]["GUID"], copies[name]["GUID"], a["GUID"]]],
                "childCardinality": "0..n",
                "isActivated": True,
                "level": "field",
                "GUID": r_guid,
                "parentCollection": tables[t_name]["GUID"],
                "childCollection": tables[name]["GUID"],
                "bucketId": bucket["GUID"],
                "hackoladeMeta": {"namingConvention": "code", "validationErrors": {}},
            })
            diff(name, a["GUID"]).update(relationshipType="Foreign Key",
                                         foreignCollection=tables[t_name]["GUID"],
                                         foreignField=parent_path, parentRelationship=r_guid)
            diff(t_name, p_attr["GUID"]).setdefault("childRelationships", []).append(r_guid)
            indexes[name].append([a["name"]])

    # ---- indexes (spec 0005, requirement 8)
    for name, cols_list in indexes.items():
        cols_list += EXTRA_INDEXES.get(name, [])
        tables[name]["Indxs"] = []
        for cols in cols_list:
            tables[name]["Indxs"].append({
                "isActivated": True,
                "index_method": "btree",
                "ifNotExist": True,
                "only": False,
                "GUID": hf.gid(MODEL, name, "index", *cols),
                "indxName": f"ix_{snake(name)}_{'_'.join(cols)}"[:63],
                "unique": False,
                "columns": [{"keyId": column(name, c)["GUID"]} for c in cols],
                "include": [],
                "where": "",
            })

    for name, local in tables.items():
        if not local["referenceDiff"]["properties"]:
            local.pop("referenceDiff")
    hf.finish(m, columns=6)
    return {FILE: m}


def hf_rel(from_file: str, to_file: str) -> str:
    import os
    return os.path.relpath(to_file, os.path.dirname(from_file)).replace(os.sep, "/")


def design_table(m: dict) -> str:
    """Markdown listing of the physical design, for the model README."""
    copies = {p["GUID"]: p for p in m["polyglotDefinitions"]["properties"]}
    lines = []
    by_guid = {c["GUID"]: c for c in m["collections"]}
    for stage, names in STAGES.items():
        lines.append(f"\n### {stage}\n")
        lines.append("| Table | From | Primary key | Unique | Foreign keys | Other indexes |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for name in names:
            c = next(x for x in m["collections"] if x["collectionName"] == name)
            cp = copies[c["ref"]]
            cols = {a["GUID"]: a["name"] for a in cp["properties"]}
            uks = ["(" + ", ".join(cols[k["keyId"]] for k in u["compositeUniqueKey"]) + ")" for u in c.get("uniqueKey", [])]
            fks = []
            for r in m["relationships"]:
                if r["childCollection"] == c["GUID"]:
                    fks.append(f"{cols[r['childField'][0][2]]} → {by_guid[r['parentCollection']]['code']}")
            fk_cols = {f.split(' ')[0] for f in fks}
            other = [", ".join(cols[k["keyId"]] for k in ix["columns"]) for ix in c.get("Indxs", [])
                     if not (len(ix["columns"]) == 1 and cols[ix["columns"][0]["keyId"]] in fk_cols)]
            frm = cp["link"].split("/")[-1].replace(".hck.json", "")
            lines.append(f"| `{c['code']}` | {frm}.{name} | entity_id | {'; '.join(uks) or '—'} | "
                         f"{'; '.join(fks) or '—'} | {'; '.join(other) or '—'} |")
    return "\n".join(lines) + "\n"
