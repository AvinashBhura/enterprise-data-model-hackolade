# migration — one-time builder

**Owner:** EDM architecture. **Delete this folder** when spec 0003 is Verified ([D5](../docs/decisions/0005-one-time-converter.md)).

These scripts wrote the first version of every model file in `src/`, from the
schemas frozen at tag `linkml-final-v0.5.0` and the new content approved in
specs 0002–0005. They never change a model after that: from then on, models
are changed in Hackolade Studio or with the Hackolade CLI.

No Hackolade licence was available when they ran, so the files are written in
the structure of files Studio saves, using only patterns seen in Hackolade's own
sample models ([D12](../docs/decisions/0012-complete-without-studio.md)). Each
file is opened and saved in Studio before it is trusted
([docs/workflows/studio-verification.md](../docs/workflows/studio-verification.md)).

| File | Does |
| --- | --- |
| `models.yaml` | What to write: each model, its entities, and the mapping rules from the old schemas (code lists, value types, polymorphic references, dropped inverses, reworded descriptions, personal-data classification) |
| `linkml_source.py` | Reads the old schemas: classes, attributes, enums, inheritance |
| `hackolade_file.py` | Writes Hackolade structures: models, containers, entities, attributes, relationships, external references, derivation |
| `build.py` | Writes the polyglot models, then the physical model. Refuses to overwrite an existing file |
| `physical.py` | Writes the Candidate Journey PostgreSQL model and lists its physical design |
| `compare.py` | Lists every difference between the old classes and the new entities, each explained or not (spec 0002 criterion 1) |
| `validate_structure.py` | Checks the written files against Hackolade's sample models: every reference resolves, and every key is one Studio itself writes |

## Commands

```bash
# Rebuild into a scratch folder and compare with what is committed (never overwrites)
python migration/build.py --out /tmp/edm-build
diff -r /tmp/edm-build/src src

# Differences from the old schemas, by scope: all, common, foundation, HR, process-core, application
python migration/compare.py --tag linkml-final-v0.5.0 --scope HR

# Structure check against Hackolade's samples
git clone https://github.com/hackolade/demo-models-read-only /tmp/hk-samples
python migration/validate_structure.py --samples /tmp/hk-samples
```

`build.py` and `compare.py` read the old schemas from tag `linkml-final-v0.5.0`
of the earlier repository, [AvinashBhura/enterprise-data-model](https://github.com/AvinashBhura/enterprise-data-model)
([D13](../docs/decisions/0013-separate-hackolade-repository.md)), with
`git archive`. Clone it, with its tags, next to this repository
(`../enterprise-data-model`), or pass `--linkml-repo PATH`, or
`--linkml-src DIR` with an extracted `src/` folder.

## What the builder decided, and where it is recorded

| Choice | Recorded in |
| --- | --- |
| Entities carry their Foundation kind's attributes | D12; `check_foundation_contract` |
| Value types are entities in CommonValueTypes, reused by external reference | D12; spec 0002 |
| AgreementParty is written inline in `Agreement.parties` | D12; spec 0002 |
| References to Entity or Organization become type + id pairs | spec 0002 requirement 14; `polymorphic_references` in `config/edm-rules.yaml` |
| ISO code lists become format rules | D3; spec 0002 requirement 13 |
| Inverse lists (`roles`, `steps`, `transitions`, `step_completions`, `events`) are dropped | spec 0002 requirement 10; spec 0004 requirement 6 |
| `classifications` is dropped; Classifiable is a marker | spec 0002, resolved question 1 |
| RoleTypeEnum gains CANDIDATE and INTERVIEWER | spec 0002 (amended) |
| Descriptions that named schema-language mechanics are reworded | `models.yaml` (`description_overrides`); listed by `compare.py` |
