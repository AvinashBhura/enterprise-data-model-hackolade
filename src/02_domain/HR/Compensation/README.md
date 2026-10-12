# HR — Compensation & Rewards

**Owner (steward):** VP Total Rewards. **May depend on:** Foundation, Common, other HR subdomain models (no cycles). Spec: [0003](../../../../specs/0003-hr-and-talent-acquisition/spec.md).

Origin of CompensationPackage. Core HR and Talent Acquisition derive it from here.

| Entity | Foundation kind | Type | Description |
| --- | --- | --- | --- |
| CompensationPackage | Agreement | Core | Total compensation structure at a point in time. |

Value types referenced from CommonValueTypes: AmountType, DocumentType, NaturalIdentifier, StateTransition

Every entity carries the attributes of its Foundation kind ([D12](../../../../docs/decisions/0012-complete-without-studio.md)).

Built by `migration/build.py` and awaiting Studio verification ([D12](../../../../docs/decisions/0012-complete-without-studio.md)): open and save it in Studio before trusting it ([runbook](../../../../docs/workflows/studio-verification.md)).
