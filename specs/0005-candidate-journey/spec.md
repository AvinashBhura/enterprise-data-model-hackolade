# 0005 — Candidate Journey physical model

Status: Implemented (2026-10-12), awaiting Studio verification
Owner: Application architecture, with HR domain steward
Decisions: [D4](../../docs/decisions/0004-generation-by-hackolade.md), [D8](../../docs/decisions/0008-candidate-journey-target.md), [D12](../../docs/decisions/0012-complete-without-studio.md)
Depends on: 0003 and 0004 Implemented; Studio verification (D12) before Verified

## Problem

The Application layer needs its first real model, built the greenfield way: derived
from Domain and Process models, then given a physical design for PostgreSQL. It
must also set the pattern for brownfield work on existing applications.

## Scope

In scope:
- `src/04_application/_shared/ApplicationShared.hck.json` (migrated: SourceSystemReference, SyncMetadata).
- `src/04_application/CandidateJourney/CandidateJourney-PostgreSQL.hck.json`.
- `docs/workflows/greenfield.md` and `docs/workflows/brownfield.md`.
- `tools/report_gaps.py` for brownfield gap reports.

Out of scope:
- Application code, APIs, data loading, process definition data.
- Any brownfield model. No existing database is in scope; the workflow is documented and the gap tool is tested on fixtures.

## Requirements

### Derivation

1. The model is derived with `polyglotDerive`, target PostgreSQL, from three polyglot models:
   - `TalentAcquisition.hck.json` — the Talent Acquisition entities and the Foundation entities they use (Person);
   - `CoreProcess.hck.json` — all six process entities;
   - `ApplicationShared.hck.json` — SourceSystemReference and SyncMetadata.
2. The derivation link to each parent is kept. Every physical change is a tracked deviation with a `deviationReason`. The link is never broken.

### Stages covered

3. The model covers the candidate journey up to the hand-over to hiring:

   | Stage | Tables |
   | --- | --- |
   | Sourcing | job_requisition, requisition_position_link, job_posting, candidate_source_channel, person, candidate, candidate_source_attribution, employee_referral, recruiting_agency, talent_pipeline |
   | Application and screening | job_application, assessment |
   | Interviewing | interview, interview_panel_assignment |
   | Selection | selection_decision, background_check, offer |
   | Journey tracking | process_definition, process_step, process_transition, process_instance, step_completion, process_event |

4. Each candidate's path is a `process_instance` whose subject is the job application (`subject_entity_type = 'JobApplication'`), with one `step_completion` per stage reached. The stage names themselves are process definition data, not schema.

### Entities owned elsewhere

5. Entities this application uses but does not own (Position, EmployeeRole, CompensationPackage, EmploymentContract, EmployeeConsentRecord) do not become tables. Each reference is an id column plus the SourceSystemReference columns (`source_system`, `source_record_id`), with no foreign key. The system of record for those entities stays elsewhere.

### Physical design

6. Inheritance: roll-down, as set in the domain model. No Foundation table.
7. Keys: `entity_id` (uuid) is the primary key of every table. Natural keys from the taxonomy (`requisition_id`, `candidate_id`...) get unique constraints.
8. Every foreign key column has an index. `lifecycle_state` is indexed on job_requisition, job_application and process_instance.
9. Arrays in the logical model become child tables (normalisation on derive): for example `state_history` becomes `<table>_state_history`, `natural_identifiers` becomes `<table>_natural_identifier`.
10. Naming: snake_case technical names from the naming convention; schema `candidate_journey`.
11. Each attribute holding personal data carries the `dataClassification` custom property (PII, Sensitive PII, or Internal). Background check results and assessment scores are Sensitive PII.
12. `enum` lists become CHECK constraints in the generated DDL.

### Brownfield pattern

13. `docs/workflows/brownfield.md` describes the steps: reverse-engineer with `revEng` or `revEngDDL`; bind tables and columns to glossary terms and set `edmMapsTo` (the Domain entity or attribute each maps to); derive an EDM-ideal physical model from the Domain; compare the two with `compMod`; refactor; keep the result as the application's model.
14. `tools/report_gaps.py` reads a reverse-engineered model and its `compMod` delta and writes a gap report: unmapped tables and columns, mapped columns whose type or enum differs from the Domain, and Domain attributes with no physical column.

## Acceptance criteria

1. The model's derivation links name the three parents. Checked in the model file by `check_layers`.
2. `forwEng --outputType=script --validateSchema=true` produces DDL that runs on PostgreSQL 16 without errors. Checked in CI against a disposable PostgreSQL container.
3. The DDL has every table in requirement 3, no table for the entities in requirement 5, and no Foundation table.
4. Every deviation has a `deviationReason`. Checked by `check_deviations`.
5. `report_gaps.py` passes its fixture tests.
6. `make check` passes.

## Validation

```bash
make check
hackolade forwEng --model=src/04_application/CandidateJourney/CandidateJourney-PostgreSQL.hck.json --path=build/ddl --outputType=script --validateSchema=true
docker run --rm -d --name cj-pg -e POSTGRES_PASSWORD=test -p 5432:5432 postgres:16
for f in build/ddl/*.sql; do PGPASSWORD=test psql -h localhost -U postgres -v ON_ERROR_STOP=1 -f "$f"; done
```

## Resolved questions

Approved by Avinash Bhura on 2026-10-12 with the recommended answers.

1. ID-plus-source references to HR entities owned elsewhere (requirement 5) are enough for now. Read-only copies need a new spec.

## Amendments — 2026-10-12, decision [D12](../../docs/decisions/0012-complete-without-studio.md)

1. **Parents (req 1).** Four: TalentAcquisition, Foundation (for `person`), CoreProcess and ApplicationShared. Person is derived from its origin, the Foundation. From ApplicationShared only SourceSystemReference becomes a table; SyncMetadata stays for application models that synchronise records.
2. **The file (req 1–2)** is written by `migration/physical.py` in the structure of a derived physical model (D12), with PostgreSQL types from the PostgreSQL plugin. Its physical design is listed in its README so it can be re-applied after a derivation in Studio.
3. **Entities owned elsewhere (req 5).** Each reference is a `uuid` column with no foreign key. The system-of-record key is a row in `source_system_reference`, which carries `referenced_entity_type` and `referenced_entity_id` (added to SourceSystemReference, with `entity_id`), unique per source system. This replaces one pair of source columns per reference.
4. **Tables (req 3)** are the 23 listed plus `source_system_reference`: 24.
5. **Keys and types (req 7).** `entity_id` and every column holding an entity_id use the PostgreSQL `uuid` type, a deviation with a reason on each table.
6. **Indexes (req 8)** also cover (`subject_entity_type`, `subject_entity_id`) on `process_instance`.
7. **Arrays (req 9).** Arrays and composite value types are `jsonb` columns: derivation without normalisation. Child tables can be introduced later by a spec if reporting needs them.
8. **Acceptance criteria 1–3** are checked during Studio verification and in CI with a licence (`make hk-validate`, DDL smoke test).
