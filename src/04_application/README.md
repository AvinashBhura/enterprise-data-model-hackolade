# Application layer

**Owner:** each application's architect. **May depend on:** every lower layer.

Physical models, one folder per application, named `<Application>-<Target>.hck.json`.

| Folder | Holds |
| --- | --- |
| [`_shared/`](_shared/README.md) | Technical constructs application models derive: SourceSystemReference, SyncMetadata |
| [`CandidateJourney/`](CandidateJourney/README.md) | The Candidate Journey PostgreSQL model |

- **Greenfield** ([docs/workflows/greenfield.md](../../docs/workflows/greenfield.md)): derive from Domain and Process polyglot models, then add the physical design as tracked deviations, each with a `deviationReason`.
- **Brownfield** ([docs/workflows/brownfield.md](../../docs/workflows/brownfield.md)): reverse-engineer the existing database, map it to Domain concepts, compare with an EDM-derived model, and report the gaps (`tools/report_gaps.py`).
