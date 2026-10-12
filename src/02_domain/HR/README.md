# HR domain

**Owner:** HR domain steward. Folders follow the subdomains of the approved HR taxonomy ([D7](../../../docs/decisions/0007-hr-folder-names.md)). One polyglot model per subdomain. Spec: [0003](../../../specs/0003-hr-and-talent-acquisition/spec.md).

| Folder | Subdomain | Origin of |
| --- | --- | --- |
| `WorkforcePlanning/` | Workforce Planning & Organization Design | Position, PositionHierarchy |
| `Compensation/` | Compensation & Rewards | CompensationPackage |
| `CoreHR/` | Core HR & Employee Records | EmployeeRole, ContractorRole, AlumniRole, ManagerRole, EmploymentContract, OnboardingChecklist, ChecklistItem |
| `Performance/` | Performance Management | PerformanceReview |
| `HRCompliance/` | HR Compliance & Employee Relations | EmployeeConsentRecord |
| `TalentAcquisition/` | Talent Acquisition | the 16 Talent Acquisition entities |
| `_shared/` | — | created only when a definition has two HR consumers and no single owner |

Dependencies between subdomain models (each arrow is a derivation of read-only entities):

```text
TalentAcquisition ──► WorkforcePlanning, CoreHR, Compensation, HRCompliance, Foundation
CoreHR ─────────────► WorkforcePlanning, Compensation, Foundation
Performance ────────► CoreHR
HRCompliance ───────► Foundation
WorkforcePlanning ──► Foundation
```

The rest of the HR taxonomy (171 data domains) is added later, one subdomain per spec.
