# HR — Core HR & Employee Records

**Owner (steward):** Head of HR Operations. **May depend on:** Foundation, Common, other HR subdomain models (no cycles). Spec: [0003](../../../../specs/0003-hr-and-talent-acquisition/spec.md).

Formerly PeopleServices (D7). Origin of the employment roles, the employment contract and onboarding checklists. Talent Acquisition and Performance derive EmployeeRole from here.

| Entity | Foundation kind | Type | Description |
| --- | --- | --- | --- |
| EmployeeRole | Role | Core | A Person's engagement as an employee. |
| ContractorRole | Role | Core | A Person engaged as an independent contractor. |
| AlumniRole | Role | Supporting | A Person's status as a former employee. |
| ManagerRole | Role | Supporting | Management authority over other Roles or units. |
| EmploymentContract | Agreement | Core | A formal employment agreement. |
| OnboardingChecklist | Document | Supporting | A template defining onboarding requirements. |
| ChecklistItem | Document | Supporting | A single checklist item — a thing that must be completed. |

Derived (read-only) from other models: CompensationPackage (Compensation), LegalEntity (Foundation), Person (Foundation), Position (WorkforcePlanning)

Value types referenced from CommonValueTypes: AmountType, DocumentType, NaturalIdentifier, StateTransition

Every entity carries the attributes of its Foundation kind ([D12](../../../../docs/decisions/0012-complete-without-studio.md)).

Built by `migration/build.py` and awaiting Studio verification ([D12](../../../../docs/decisions/0012-complete-without-studio.md)): open and save it in Studio before trusting it ([runbook](../../../../docs/workflows/studio-verification.md)).
