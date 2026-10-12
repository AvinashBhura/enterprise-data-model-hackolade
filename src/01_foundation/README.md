# Foundation layer

**Owner:** EDM architecture. **May depend on:** Common only.

`Foundation.hck.json` holds the root `Entity` and the 11 Foundation concepts. Every Domain, Process and Application entity specialises exactly one of them (`foundationKind`) and carries its attributes ([D12](../../docs/decisions/0012-complete-without-studio.md), `make check-foundation-contract`). Spec: [0002](../../specs/0002-foundation-and-common/spec.md).

| Entity | Foundation kind | Type | Description |
| --- | --- | --- | --- |
| Entity | Entity | Core | The semantic anchor of the EDM. |
| Person | Person | Core | A human being. |
| Organization | Organization | Core | A formal body. |
| LegalEntity | LegalEntity | Core | A jurisdictional legal entity — company, NGO, government agency, subsidiary, joint venture. |
| OrganizationalUnit | OrganizationalUnit | Core | A unit within a legal entity — business unit, division, department, group. |
| Team | Team | Core | A purposeful group whose identity is defined by shared purpose and membership. |
| Role | Role | Core | A time-bound engagement. |
| Activity | Activity | Core | A time-bound action or event. |
| Agreement | Agreement | Core | A formal commitment. |
| Asset | Asset | Core | A thing of value. |
| Address | Address | Core | A structured postal or physical address. |
| Document | Document | Core | A formal informational artifact. |
| Period | Period | Core | A defined time interval. |

Value types referenced from CommonValueTypes: AmountType, DocumentType, NaturalIdentifier, StateTransition

- `Entity` and `Organization` are never tables (`edmAbstract`; set Hackolade's *Polyglot only* flag on them too). References to Organization are pairs restricted to LegalEntity and OrganizationalUnit.
- LegalEntity and OrganizationalUnit carry Organization's attributes.
- `Agreement.parties` holds the parties inline (party type and id, capacity, signing).
- Base-type attributes follow the contracts in `config/edm-rules.yaml` (`edmComposes`, D2). Classifiable is a marker: classifications are rows in `CommonTaxonomy.TransactionHierarchy`.

Built by `migration/build.py` and awaiting Studio verification ([D12](../../docs/decisions/0012-complete-without-studio.md)): open and save it in Studio before trusting it ([runbook](../../docs/workflows/studio-verification.md)).

Changes here are rare and need EDM steering approval: every other layer depends on this one.
