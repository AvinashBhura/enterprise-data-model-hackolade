# Application `_shared`

**Owner:** application architecture. **May depend on:** Foundation, Common. Spec: [0005](../../../specs/0005-candidate-journey/spec.md).

`ApplicationShared.hck.json` holds technical constructs that application models derive. They are not EDM business concepts, so their Foundation kind is `none` (`foundation.technical_paths` in `config/edm-rules.yaml`).

| Entity | Foundation kind | Type | Description |
| --- | --- | --- | --- |
| SourceSystemReference | none | Supporting | A reference to an entity's representation in a source system. |
| SyncMetadata | none | Supporting | A reusable value type capturing sync metadata. |

- SourceSystemReference maps an EDM entity (`referenced_entity_type`, `referenced_entity_id`) to its key in a system of record. An application that uses an entity it does not own keeps only the entity_id, and finds the source key here.
- SyncMetadata records how a record is synchronised with a source system.

Built by `migration/build.py` and awaiting Studio verification ([D12](../../../docs/decisions/0012-complete-without-studio.md)): open and save it in Studio before trusting it ([runbook](../../../docs/workflows/studio-verification.md)).
