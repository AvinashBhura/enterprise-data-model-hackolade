# Studio verification runbook

Every model file in `src/` was written by `migration/build.py` without a
Hackolade licence ([D12](../decisions/0012-complete-without-studio.md)). They
follow the structure of Studio-saved files and pass
`migration/validate_structure.py`, but no copy of Studio has opened them yet.
This runbook is what to do once a licence is available. When it is done,
specs 0002–0005 can be marked Verified.

Allow about half a day. Work on a branch, for example `verify/studio`.

## 0. Before you start

1. Hackolade Studio **8.13.0 or later**, Workgroup edition (D9), with the
   **PostgreSQL** plugin (Help > Plugin Manager).
2. `make hackolade-config FORCE=1`, then restart Studio. Set the naming
   conventions it prints (Tools > Options > Naming Conventions).
3. `make check` and `make test` pass on the branch.
4. Keep a copy of `src/` (`cp -R src /tmp/src-before-studio`), to compare what
   Studio changes on save.

Record results in `spikes/results/RESULTS.md` (template in
[spikes/README.md](../../spikes/README.md)).

## 1. Open and save each model, lowest layer first

Open, check, save (Cmd/Ctrl+S), close. In this order, because each model
reads the ones before it:

| # | Model | Check after opening |
| --- | --- | --- |
| 1 | `01_foundation/common/CommonValueTypes` | 5 entities; Properties > EDM tab shows `edmValueType` |
| 2 | `01_foundation/common/CommonTaxonomy` | 5 entities, 8 relationships; composite key on TaxonomyClosure; unique key on TaxonomyVersion |
| 3 | `01_foundation/Foundation` | 13 entities; `natural_identifiers`, `state_history`, `total_value` resolve to CommonValueTypes (right-click > Refresh external references); `Agreement.parties` shows its nested fields |
| 4 | `02_domain/HR/WorkforcePlanning` | Position, PositionHierarchy; derived Person and OrganizationalUnit shown as read-only |
| 5 | `02_domain/HR/Compensation` | CompensationPackage |
| 6 | `02_domain/HR/CoreHR` | 7 entities; derived Position, CompensationPackage, LegalEntity, Person |
| 7 | `02_domain/HR/Performance` | PerformanceReview; derived EmployeeRole |
| 8 | `02_domain/HR/HRCompliance` | EmployeeConsentRecord; derived Person, Period |
| 9 | `02_domain/HR/TalentAcquisition` | 16 entities; 7 derived entities; enum values on `lifecycle_state` |
| 10 | `03_process/_core/CoreProcess` | 6 entities; derived Person, Role |
| 11 | `04_application/_shared/ApplicationShared` | 2 entities |
| 12 | `04_application/CandidateJourney/CandidateJourney-PostgreSQL` | 24 tables in schema `candidate_journey`; uuid primary keys; indexes; foreign keys |

For each: note any error or warning dialog word for word. Then:

```bash
make check
python migration/validate_structure.py --samples <clone of hackolade/demo-models-read-only>
git diff --stat src/
```

After saving, `applicationInformation.version` shows your Studio version.
Then clear **Built by** (`edmBuiltBy`) on the model's EDM tab and save again:
the file is now Studio's, not the builder's.

**If a file does not open:** stop, keep the error text, and rebuild that model
in Studio by hand from its README and spec (the README lists every entity;
`migration/models.yaml` lists every new attribute). Then continue.

## 2. Mark the abstract entities

In Foundation, select `Entity` and `Organization`, and tick **Polyglot only**
(entity Properties). Save. They then never derive into a physical model
(D12, decision 5).

## 3. Confirm the custom properties

Open a few entities and attributes. The EDM tab must show the values the
builder wrote: `layer`, `foundationKind`, `entityType`, `steward`,
`edmComposes`, `edmConnects` (junctions), `valueDefinitions` (enums),
`dataClassification` (Person, Candidate, Assessment...). If a value is
missing, the property keyword or type in `hackolade/customProperties/` does
not match what Studio expects: fix the configuration, not the model.

## 4. Derivation and DDL

1. Re-derive the Candidate Journey to a scratch file and compare it with the
   committed one:

   ```bash
   hackolade polyglotDerive --target=PostgreSQL --pathType=relative \
     --polyglotmodels="src/02_domain/HR/TalentAcquisition/TalentAcquisition.hck.json;src/01_foundation/Foundation.hck.json;src/03_process/_core/CoreProcess.hck.json;src/04_application/_shared/ApplicationShared.hck.json" \
     --targetmodel=/tmp/cj-derived.hck.json
   hackolade compMod --model1=/tmp/cj-derived.hck.json \
     --model2=src/04_application/CandidateJourney/CandidateJourney-PostgreSQL.hck.json \
     --deltaModel=/tmp/cj-delta.hck.json
   ```

   Differences should be only the physical design in the model's README. If
   Studio's own derivation is cleaner, keep it and re-apply that design.
2. Generate the DDL and run it:

   ```bash
   make hk-validate
   docker run --rm -d --name cj-pg -e POSTGRES_PASSWORD=test -p 5432:5432 postgres:16
   for f in build/ddl/**/*.sql; do PGPASSWORD=test psql -h localhost -U postgres -v ON_ERROR_STOP=1 -f "$f"; done
   ```

   Expect 24 tables, no `entity`, `organization`, `role`, `document` or
   `activity` table, CHECK constraints for the enums, `jsonb` for arrays.
3. Trial-derive Foundation, TalentAcquisition and CoreProcess to PostgreSQL
   (spec 0002 criterion 3, spec 0003 criterion 5, spec 0004 criterion 3) and
   attach the DDL to the pull request.
4. `make hk-stale`: no model should be behind its parents.

## 5. Spikes still worth running

From [spikes/README.md](../../spikes/README.md):

- **T1** (supertype group on a derived entity, roll-down). If it passes, a
  follow-up spec can replace the carried Foundation attributes with supertype
  groups (D12 consequences).
- **T2** (external reference as supertype).
- **T5** (custom properties inside the Docker CLI image), needed before
  relying on the CI Hackolade stages.

T3 and T4 are answered by steps 1 and 4.

## 6. CI with a licence

1. Add the concurrent licence key as the repository secret `HACKOLADE_LICENSE`.
2. Confirm `hackolade/hck-cli:8.13.0` exists on Docker Hub; otherwise pin the
   first 8.13+ tag in `ci/Dockerfile`.
3. Open a test pull request touching `src/`: `hackolade.yml` must run the stale
   gate, schema gate, DDL smoke test and change report. Check what an empty
   `compMod` delta looks like and adjust `ci/delta.py --empty` if needed.
4. Run spec 0006's test pull requests and a test tag; record the links in the
   spec.

## 7. Close out

1. In `config/edm-rules.yaml`, set `format.accept_builder_output: false`.
   `make check` must still pass (every file now saved by Studio 8.13+).
2. Mark D12 Accepted (or replace it, if T1 passed and a follow-up spec is
   approved).
3. Set specs 0002–0005 to Verified, with the date and the pull request link.
4. Delete `migration/` and `spikes/` (spec 0002, D5), and the
   `TestModelFiles` skip path then applies.
