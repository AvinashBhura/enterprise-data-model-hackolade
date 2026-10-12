# HR — Performance Management

**Owner (steward):** Head of Performance & Talent. **May depend on:** Foundation, Common, other HR subdomain models (no cycles). Spec: [0003](../../../../specs/0003-hr-and-talent-acquisition/spec.md).

Origin of PerformanceReview.

| Entity | Foundation kind | Type | Description |
| --- | --- | --- | --- |
| PerformanceReview | Activity | Core | A periodic performance evaluation event for an employee. |

Derived (read-only) from other models: EmployeeRole (CoreHR)

Value types referenced from CommonValueTypes: NaturalIdentifier, StateTransition

Every entity carries the attributes of its Foundation kind ([D12](../../../../docs/decisions/0012-complete-without-studio.md)).

Built by `migration/build.py` and awaiting Studio verification ([D12](../../../../docs/decisions/0012-complete-without-studio.md)): open and save it in Studio before trusting it ([runbook](../../../../docs/workflows/studio-verification.md)).
