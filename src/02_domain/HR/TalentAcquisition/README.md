# HR — Talent Acquisition

**Owner (steward):** VP Talent Acquisition / Head of Recruiting. **May depend on:** Foundation, Common, other HR subdomain models (no cycles). Spec: [0003](../../../../specs/0003-hr-and-talent-acquisition/spec.md).

The 15 data domains of the HR taxonomy plus SelectionDecision: requisition through offer. Entities owned by other subdomains are derived from their origin models, read-only; relationships point to the derived copies.

| Entity | Foundation kind | Type | Description |
| --- | --- | --- | --- |
| JobRequisition | Document | Core | The approved request to fill one or more positions. |
| Candidate | Role | Core | A person engaged with the enterprise as a job seeker. |
| JobApplication | Document | Core | A candidate's application to a requisition. |
| JobPosting | Document | Core | The externally published advertisement of a requisition. |
| Offer | Agreement | Core | A pre-employment offer letter. |
| Interview | Activity | Supporting | An interview of a candidate for an application. |
| Assessment | Activity | Supporting | A structured evaluation of a candidate for an application, such as a coding test or work sample. |
| BackgroundCheck | Activity | Supporting | Pre-employment screening of a candidate. |
| CandidateSourceChannel | Document | Supporting | A channel through which candidates arrive; drives sourcing return-on-investment analysis. |
| RecruitingAgency | LegalEntity | Supporting | An external recruiting partner: a legal entity engaged to find candidates. |
| TalentPipeline | Document | Supporting | A curated pool of prospective candidates for future requisitions. |
| EmployeeReferral | Document | Supporting | A candidate referred by an employee, with referral-bonus tracking. |
| InterviewPanelAssignment | Role | Bridge/Junction | Which employees interview in which interviews (many-to-many), with each interviewer's own feedback and recommendation. |
| RequisitionPositionLink | Document | Bridge/Junction | Which positions a requisition fills (many-to-many); a requisition can cover several identical positions. |
| CandidateSourceAttribution | Document | Bridge/Junction | Multi-touch attribution of a candidate to the channels that reached them (many-to-many). |
| SelectionDecision | Activity | Core | A hiring decision on a job application at a stage of the process: advance, reject, hold or hire, with who decided and why. |

Derived (read-only) from other models: CompensationPackage (Compensation), EmployeeConsentRecord (HRCompliance), EmployeeRole (CoreHR), EmploymentContract (CoreHR), LegalEntity (Foundation), Person (Foundation), Position (WorkforcePlanning)

Value types referenced from CommonValueTypes: AmountType, DocumentType, NaturalIdentifier, StateTransition

Every entity carries the attributes of its Foundation kind ([D12](../../../../docs/decisions/0012-complete-without-studio.md)).

Notes:
- Candidate is a Role held by a Person (`held_by_person`, required). On hire the person takes an EmployeeRole.
- Junctions name the two entities they connect in `edmConnects` (`make check-junctions`).
- `RecruitingAgency.vendor_contract_id` is a typed key until Procurement is migrated (D6).
- Natural keys from the taxonomy (`requisition_id`...) are unique keys; they can also be recorded in `natural_identifiers`.
- A job application's progress through the hiring stages is a process instance (Process layer), not state on these entities.

Built by `migration/build.py` and awaiting Studio verification ([D12](../../../../docs/decisions/0012-complete-without-studio.md)): open and save it in Studio before trusting it ([runbook](../../../../docs/workflows/studio-verification.md)).
