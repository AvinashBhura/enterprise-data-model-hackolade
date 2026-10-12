# Candidate Journey (PostgreSQL)

**Owner:** application architecture, with the HR domain steward. **May depend on:** every lower layer. Spec: [0005](../../../specs/0005-candidate-journey/spec.md). Decision: [D8](../../../docs/decisions/0008-candidate-journey-target.md).

`CandidateJourney-PostgreSQL.hck.json` is the physical model of the candidate journey: sourcing, application and screening, interviewing and selection, up to the hand-over to hiring. It is built the greenfield way ([docs/workflows/greenfield.md](../../../docs/workflows/greenfield.md)): derived from four polyglot models, then given a physical design.

| Parent model | Tables derived from it |
| --- | --- |
| `02_domain/HR/TalentAcquisition` | the 16 Talent Acquisition entities |
| `01_foundation/Foundation` | person |
| `03_process/_core/CoreProcess` | the 6 process entities |
| `04_application/_shared/ApplicationShared` | source_system_reference |

The derivation link to each parent is kept: every table points to its logical entity, and every physical change is a tracked deviation with a `deviationReason`.

## How the journey is recorded

Each candidate's path is a `process_instance` whose subject is the job application (`subject_entity_type = 'JobApplication'`, `subject_entity_id` = the application's `entity_id`), with one `step_completion` per stage reached and `process_event` rows for what happened. The stage names are process definition data (`process_definition`, `process_step`, `process_transition`), not schema. Each instance stays bound to the definition version it started with.

## Physical design

These choices are local to this model. They are listed here so they can be re-applied if the model is re-derived in Studio ([D12](../../../docs/decisions/0012-complete-without-studio.md)).

1. **Schema:** one schema, `candidate_journey`. Technical names are snake_case (table `job_requisition`, column `hiring_manager_role`), at most 63 characters.
2. **Inheritance:** roll-down. Each table carries its Foundation kind's columns; there is no Foundation table except `person`, which the journey needs as a real record. No `entity`, `organization`, `role`, `document` or `activity` table.
3. **Keys:** `entity_id` (`uuid`) is the primary key of every table, named `<table>_pkey`. Natural keys from the HR taxonomy are unique constraints, named `<table>_<column>_key`.
4. **uuid columns:** `entity_id` and every column holding an `entity_id` use the PostgreSQL `uuid` type (the logical model has text with the UUID pattern). This is the one deviation on each table, with its reason.
5. **Foreign keys:** only between tables of this model. A reference to an entity this application does not own (Position, EmployeeRole, CompensationPackage, EmploymentContract, EmployeeConsentRecord, LegalEntity, Role) is a `uuid` column with no foreign key. Its key in the system of record is a row in `source_system_reference` (`referenced_entity_type`, `referenced_entity_id`, `source_system`, `source_record_id`).
6. **Indexes:** every foreign-key column; `lifecycle_state` on `job_requisition`, `job_application` and `process_instance`; (`subject_entity_type`, `subject_entity_id`) on `process_instance`.
7. **Arrays and composite values:** stored as `jsonb` (derivation without normalisation): arrays such as `natural_identifiers`, `state_history`, `participants`, `parties`, `addresses`, and value types such as amounts (`total_value`, `sign_on_bonus`, `cost_per_hire`). Their JSON shape is the logical structure (for an amount: `value`, `currency`, `precision`). 75 such columns in all.
8. **Closed lists:** every `enum` becomes a CHECK constraint in the generated DDL.
9. **Personal data:** columns carry `dataClassification` from the logical model (PII, Sensitive PII). Background-check results and assessment scores are Sensitive PII.

### Sourcing

| Table | From | Primary key | Unique | Foreign keys | Other indexes |
| --- | --- | --- | --- | --- | --- |
| `job_requisition` | TalentAcquisition.JobRequisition | entity_id | (requisition_id) | replaces_document → job_requisition | lifecycle_state |
| `requisition_position_link` | TalentAcquisition.RequisitionPositionLink | entity_id | (link_id) | job_requisition → job_requisition; replaces_document → requisition_position_link | — |
| `job_posting` | TalentAcquisition.JobPosting | entity_id | (posting_id) | job_requisition → job_requisition; replaces_document → job_posting | — |
| `candidate_source_channel` | TalentAcquisition.CandidateSourceChannel | entity_id | (channel_id) | replaces_document → candidate_source_channel | — |
| `person` | Foundation.Person | entity_id | — | — | — |
| `candidate` | TalentAcquisition.Candidate | entity_id | (candidate_id) | source_channel → candidate_source_channel; held_by_person → person | — |
| `candidate_source_attribution` | TalentAcquisition.CandidateSourceAttribution | entity_id | (attribution_id) | candidate → candidate; source_channel → candidate_source_channel; replaces_document → candidate_source_attribution | — |
| `employee_referral` | TalentAcquisition.EmployeeReferral | entity_id | (referral_id) | candidate → candidate; job_requisition → job_requisition; replaces_document → employee_referral | — |
| `recruiting_agency` | TalentAcquisition.RecruitingAgency | entity_id | (agency_id) | — | — |
| `talent_pipeline` | TalentAcquisition.TalentPipeline | entity_id | (pipeline_id) | replaces_document → talent_pipeline | — |

### Application and screening

| Table | From | Primary key | Unique | Foreign keys | Other indexes |
| --- | --- | --- | --- | --- | --- |
| `job_application` | TalentAcquisition.JobApplication | entity_id | (application_id) | candidate → candidate; job_requisition → job_requisition; replaces_document → job_application | lifecycle_state |
| `assessment` | TalentAcquisition.Assessment | entity_id | (assessment_id) | job_application → job_application | — |

### Interviewing

| Table | From | Primary key | Unique | Foreign keys | Other indexes |
| --- | --- | --- | --- | --- | --- |
| `interview` | TalentAcquisition.Interview | entity_id | (interview_id) | job_application → job_application | — |
| `interview_panel_assignment` | TalentAcquisition.InterviewPanelAssignment | entity_id | (assignment_id) | interview → interview; held_by_person → person | — |

### Selection

| Table | From | Primary key | Unique | Foreign keys | Other indexes |
| --- | --- | --- | --- | --- | --- |
| `selection_decision` | TalentAcquisition.SelectionDecision | entity_id | (decision_id) | job_application → job_application | — |
| `background_check` | TalentAcquisition.BackgroundCheck | entity_id | (check_id) | candidate → candidate | — |
| `offer` | TalentAcquisition.Offer | entity_id | — | candidate → person | — |

### Journey tracking

| Table | From | Primary key | Unique | Foreign keys | Other indexes |
| --- | --- | --- | --- | --- | --- |
| `process_definition` | CoreProcess.ProcessDefinition | entity_id | — | replaces_document → process_definition; replaces_definition → process_definition | — |
| `process_step` | CoreProcess.ProcessStep | entity_id | — | process_definition → process_definition | — |
| `process_transition` | CoreProcess.ProcessTransition | entity_id | — | replaces_document → process_transition; from_step → process_step; to_step → process_step | — |
| `process_instance` | CoreProcess.ProcessInstance | entity_id | — | definition → process_definition; initiated_by → person; migrated_to_instance → process_instance; migrated_from_instance → process_instance | lifecycle_state; subject_entity_type, subject_entity_id |
| `step_completion` | CoreProcess.StepCompletion | entity_id | — | step → process_step; process_instance_id → process_instance; completed_by_person → person | — |
| `process_event` | CoreProcess.ProcessEvent | entity_id | — | process_instance_id → process_instance; actor_person → person; related_step → process_step | — |

### Source of record

| Table | From | Primary key | Unique | Foreign keys | Other indexes |
| --- | --- | --- | --- | --- | --- |
| `source_system_reference` | ApplicationShared.SourceSystemReference | entity_id | (referenced_entity_type, referenced_entity_id, source_system) | — | — |

## Generating the DDL

```bash
make hk-validate     # forwEng --validateSchema=true for this model
hackolade forwEng --model=src/04_application/CandidateJourney/CandidateJourney-PostgreSQL.hck.json \
  --path=build/ddl --outputType=script --validateSchema=true
```

The DDL is a build output: it is not committed here (D4). The application's own repository commits the DDL it deploys.

Built by `migration/build.py` and awaiting Studio verification ([D12](../../../docs/decisions/0012-complete-without-studio.md)): open and save it in Studio before trusting it ([runbook](../../../docs/workflows/studio-verification.md)).
