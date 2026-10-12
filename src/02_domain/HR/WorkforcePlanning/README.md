# HR — Workforce Planning & Organization Design

**Owner (steward):** VP People Strategy / Head of Workforce Planning. **May depend on:** Foundation, Common, other HR subdomain models (no cycles). Spec: [0003](../../../../specs/0003-hr-and-talent-acquisition/spec.md).

Origin of Position and PositionHierarchy (moved from PeopleServices, D7). Talent Acquisition and Core HR derive Position from here.

| Entity | Foundation kind | Type | Description |
| --- | --- | --- | --- |
| Position | Role | Core | A job slot defined within an OrganizationalUnit. |
| PositionHierarchy | Document | Supporting | A reporting relationship between two Positions. |

Derived (read-only) from other models: OrganizationalUnit (Foundation), Person (Foundation)

Value types referenced from CommonValueTypes: AmountType, NaturalIdentifier, StateTransition

Every entity carries the attributes of its Foundation kind ([D12](../../../../docs/decisions/0012-complete-without-studio.md)).

Built by `migration/build.py` and awaiting Studio verification ([D12](../../../../docs/decisions/0012-complete-without-studio.md)): open and save it in Studio before trusting it ([runbook](../../../../docs/workflows/studio-verification.md)).
