# 0003 — HR domain and Talent Acquisition

Status: Implemented (2026-10-12), awaiting Studio verification
Owner: HR domain steward, with EDM architecture
Decisions: [D1](../../docs/decisions/0001-cross-file-specialisation.md), [D2](../../docs/decisions/0002-base-type-attributes-on-entities.md), [D3](../../docs/decisions/0003-enumerations-on-attributes.md), [D6](../../docs/decisions/0006-migration-scope.md), [D7](../../docs/decisions/0007-hr-folder-names.md), [D12](../../docs/decisions/0012-complete-without-studio.md)
Depends on: 0002 Implemented; Studio verification (D12) before Verified

## Problem

The HR domain must move to Hackolade, and Talent Acquisition must be modelled
from the approved HR taxonomy. Talent Acquisition uses entities owned by other
HR subdomains, so those owners must exist first, each in its own model.

## Scope

In scope:
- Migrate the existing HR LinkML entities into subdomain models named after the HR taxonomy (D7).
- Create the Talent Acquisition model: all 15 data domains from the taxonomy, plus Selection Decision (resolved question 1).
- Create the smallest origin models Talent Acquisition needs (one new entity: Employee Consent Record).

Out of scope:
- The rest of the HR taxonomy (171 data domains). Each subdomain is added later under its own spec.
- Non-HR domains (frozen, D6).

## Requirements

### Folder and model layout

1. One polyglot model per subdomain, in a folder named after the subdomain:

   | Folder | Model | Entities |
   | --- | --- | --- |
   | `HR/CoreHR/` | `CoreHR.hck.json` | EmployeeRole, ContractorRole, AlumniRole, ManagerRole, EmploymentContract, OnboardingChecklist, ChecklistItem (migrated) |
   | `HR/WorkforcePlanning/` | `WorkforcePlanning.hck.json` | Position, PositionHierarchy (migrated; moved from PeopleServices per D7) |
   | `HR/Compensation/` | `Compensation.hck.json` | CompensationPackage (migrated) |
   | `HR/Performance/` | `Performance.hck.json` | PerformanceReview (migrated) |
   | `HR/HRCompliance/` | `HRCompliance.hck.json` | EmployeeConsentRecord (new, from the taxonomy) |
   | `HR/TalentAcquisition/` | `TalentAcquisition.hck.json` | The 15 Talent Acquisition data domains; Offer is migrated, the other 14 are new |
   | `HR/_shared/` | none yet | Created only when a definition has two HR consumers and no single owner |

2. Each model sets `edmLayer: Domain`, `edmDomain: HR` and its subdomain in model-level custom properties.

### Specialising the Foundation (D1)

3. Each model derives from `Foundation.hck.json` only the Foundation entities it needs: those its entities specialise, those its relationships point to, and their supertypes (deriving LegalEntity brings Organization). It creates one local supertype group per Foundation kind it specialises. Example: Talent Acquisition derives Role, Agreement, Activity, Document, Organization (supertypes) and Person (target of `Candidate.held_by_person`).
4. Derived Foundation entities in a domain model are not edited (no deviations). `check_deviations` enforces this.
5. Supertype groups in domain models use the **roll-down** strategy, so physical models get one table per domain entity carrying the Foundation attributes, with no Foundation tables. Applications may choose otherwise (spec 0005).
6. If spike T2 passes, requirements 3 and 4 change to: each model references Foundation entities by external reference instead of deriving them. This spec is then updated and re-approved.

### Talent Acquisition entities

7. All 15 data domains from the HR taxonomy, with their Foundation kind and entity type as approved:

   | Entity | Type | Foundation kind | Connects |
   | --- | --- | --- | --- |
   | Job Requisition | Core | Document | |
   | Candidate | Core | Role | |
   | Job Application | Core | Document | |
   | Job Posting | Core | Document | |
   | Offer | Core | Agreement | |
   | Interview | Supporting | Activity | |
   | Assessment | Supporting | Activity | |
   | Background Check | Supporting | Activity | |
   | Candidate Source Channel | Supporting | Document | |
   | Recruiting Agency | Supporting | Organization | |
   | Talent Pipeline | Supporting | Document | |
   | Employee Referral | Supporting | Document | |
   | Interview Panel Assignment | Junction | Role | Interview ↔ Employee Role |
   | Requisition Position Link | Junction | Document | Job Requisition ↔ Position |
   | Candidate Source Attribution | Junction | Document | Candidate ↔ Candidate Source Channel |

8. Attributes come from the taxonomy's key attributes, adjusted to EDM conventions:
   - `_ref` attributes become relationships to the owning entity (inside the model) or to the referenced entity in its origin model (across models).
   - Status attributes become `lifecycle_state` with the entity's own `enum` (D3), using the values listed in the taxonomy.
   - Base-type attributes follow the contracts (D2).
   - The taxonomy's "(NK)" attribute becomes the natural key, recorded through `natural_identifiers` (Identifiable) and also kept as a unique attribute.
9. Candidate is a Role held by a Person: `held_by_person` → Foundation Person. The `person_ref` attribute in the taxonomy is replaced by this inherited relationship.
10. Offer is migrated from LinkML, keeping its attributes and `OfferLifecycleStateEnum` values. Taxonomy attributes not already on Offer (`equity_grant`, `bonus_target`) are added.

### Cross-model references

11. Talent Acquisition reads other subdomains' entities by external reference only, never by copy:

    | From Talent Acquisition | To | Owner |
    | --- | --- | --- |
    | Job Requisition, Requisition Position Link | Position | WorkforcePlanning |
    | Interview Panel Assignment, Employee Referral, Job Requisition (hiring manager, recruiter) | EmployeeRole | CoreHR |
    | Offer (proposed compensation) | CompensationPackage | Compensation |
    | Offer (resulting contract) | EmploymentContract | CoreHR |
    | Background Check (consent) | EmployeeConsentRecord | HRCompliance |

12. Recruiting Agency's contract points to Procurement's vendor contract, which is frozen (D6). Until Procurement is migrated, it is a typed key `vendor_contract_id` with a description naming the future target.

### Migrated HR entities

13. Every migrated entity keeps its LinkML attributes, descriptions and enum values. Changes allowed: those required by D2, D3 and the polymorphic-reference pattern (spec 0002), and the folder move in D7.

## Acceptance criteria

1. All 16 Talent Acquisition data domains (15 from the taxonomy plus Selection Decision) exist with the Foundation kind and entity type in requirement 7. Checked by `check_metadata` and `check_foundation_kind`.
2. `migration/compare.py` shows no unexplained difference between the LinkML HR entities and the migrated ones.
3. Every junction has its own key and exactly two relationships. Checked by `check_junctions`.
4. No entity is defined in more than one model. Checked by `check_ownership`.
5. A trial derivation of Talent Acquisition to PostgreSQL produces one table per Talent Acquisition entity (16), a `person` table, tables for the entities referenced in requirement 11, and no table for a Foundation entity used only as a supertype. Every relationship in requirement 11 is a foreign key. Output attached to the pull request.
6. `make check` passes and Studio opens every model without errors.

## Validation

```bash
python migration/compare.py --tag linkml-final-v0.5.0 --scope HR
make check
hackolade polyglotDerive --target=PostgreSQL --polyglotmodels=src/02_domain/HR/TalentAcquisition/TalentAcquisition.hck.json --targetmodel=/tmp/ta-pg.hck.json
```

## Resolved questions

Approved by Avinash Bhura on 2026-10-12 with the recommended answers.

1. Selection decision: option A. **Selection Decision** (Core, Foundation kind Activity) is added to Talent Acquisition, with: `decision_id` (natural key), relationship to Job Application, `decided_by` (relationship to EmployeeRole), `decided_at`, `outcome` (`enum`: ADVANCE, REJECT, HOLD, HIRE), `reason_code`, `rationale`. The HR taxonomy workbook gets the same row. Talent Acquisition then has 16 data domains.
2. The business name is "Talent Pipeline".

## Amendments — 2026-10-12, decision [D12](../../docs/decisions/0012-complete-without-studio.md)

1. **Specialising the Foundation (req 3–6).** Entities carry their Foundation kind's attributes (D12) instead of local supertype groups. A model derives from other models only the entities its relationships point to (for example Person, Position, EmployeeRole). Derived entities are not edited.
2. **Names (req 7).** PascalCase business names: JobRequisition, Candidate, JobApplication, JobPosting, Offer, Interview, Assessment, BackgroundCheck, CandidateSourceChannel, RecruitingAgency, TalentPipeline, EmployeeReferral, InterviewPanelAssignment, RequisitionPositionLink, CandidateSourceAttribution, SelectionDecision. Each carries `sourceTaxonomyRef` to its taxonomy row.
3. **RecruitingAgency** specialises LegalEntity (Organization is abstract), with `organization_type` narrowed to `PARTNER`. Its `agency_name` is the inherited `legal_name`.
4. **Kind narrowing.** Candidate: `role_type` CANDIDATE, `held_by_person` required. InterviewPanelAssignment: INTERVIEWER. Interview: `activity_type` MEETING; Assessment: REVIEW; BackgroundCheck: TASK; SelectionDecision: EVENT, with the inherited `outcome` closed to ADVANCE, REJECT, HOLD, HIRE.
5. **Attributes (req 8).** `_ref` attributes become relationships named without the suffix (`position_ref` → `position`); `*_role` attributes become relationships to EmployeeRole. Entities with taxonomy status values get them as their `lifecycle_state` enum (JobRequisition, Candidate). Entities without status values keep their kind's lifecycle (JobApplication, EmployeeReferral). Interview uses the inherited `scheduled_start` for `scheduled_at`, and `format` is named `interview_format`. BackgroundCheck's `provider_org` is `provider_organization` (→ LegalEntity) and its consent is `consent_record` (→ EmployeeConsentRecord). Candidate's `talent_pool_refs` is `talent_pipelines`, a list of TalentPipeline entity_id values. Offer keeps its original `candidate` (→ Person).
6. **Junctions.** Each names the two entities it connects in `edmConnects` (spec 0001 amendment 2). RequisitionPositionLink also keeps `vacated_by_role` (→ EmployeeRole).
7. **EmployeeConsentRecord** is in HRCompliance as specified; its `retention_period` is a relationship to Period.
8. **Acceptance criterion 5** (trial derivation) is checked during Studio verification. Criterion 2: `python migration/compare.py --scope HR`.
