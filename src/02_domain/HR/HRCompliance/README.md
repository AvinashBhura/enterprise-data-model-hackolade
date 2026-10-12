# HR — HR Compliance & Employee Relations

**Owner (steward):** Head of HR Compliance. **May depend on:** Foundation, Common, other HR subdomain models (no cycles). Spec: [0003](../../../../specs/0003-hr-and-talent-acquisition/spec.md).

Origin of EmployeeConsentRecord (new, from the HR taxonomy). Talent Acquisition uses it for background-check consent.

| Entity | Foundation kind | Type | Description |
| --- | --- | --- | --- |
| EmployeeConsentRecord | Document | Supporting | GDPR/CCPA consent a person has given (or withdrawn) for a stated purpose, such as data processing, monitoring or a background check. |

Derived (read-only) from other models: Period (Foundation), Person (Foundation)

Value types referenced from CommonValueTypes: NaturalIdentifier, StateTransition

Every entity carries the attributes of its Foundation kind ([D12](../../../../docs/decisions/0012-complete-without-studio.md)).

Built by `migration/build.py` and awaiting Studio verification ([D12](../../../../docs/decisions/0012-complete-without-studio.md)): open and save it in Studio before trusting it ([runbook](../../../../docs/workflows/studio-verification.md)).
