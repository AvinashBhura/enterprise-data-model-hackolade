# Process layer

**Owner:** EDM architecture. **May depend on:** Foundation, Common (and Domain models, though the core model needs none).

| Folder | Holds |
| --- | --- |
| [`_core/`](_core/README.md) | The core process model: definitions, steps, transitions, instances, step completions, events |

Workflow state lives here, never on Domain entities. Business-specific processes are data in these entities, not schemas.
