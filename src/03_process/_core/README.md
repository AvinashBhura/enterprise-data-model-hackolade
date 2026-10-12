# Core process model

**Owner:** EDM architecture. **May depend on:** Foundation, Common. Spec: [0004](../../../specs/0004-core-process-model/spec.md).

`CoreProcess.hck.json` separates workflow state from entity state. A process definition is data, created by applications; there is no business-specific process here.

| Entity | Foundation kind | Type | Description |
| --- | --- | --- | --- |
| ProcessDefinition | Document | Core | A versioned workflow specification. |
| ProcessStep | Activity | Core | A single step within a ProcessDefinition. |
| ProcessTransition | Document | Supporting | An allowed transition between two ProcessSteps. |
| ProcessInstance | Activity | Core | A live execution of a ProcessDefinition. |
| StepCompletion | Activity | Supporting | Execution record for a step within an instance. |
| ProcessEvent | Activity | Supporting | An event recorded in a ProcessInstance's lifecycle. |

Derived (read-only) from other models: Person (Foundation), Role (Foundation)

Value types referenced from CommonValueTypes: NaturalIdentifier, StateTransition

- A ProcessInstance is bound to one definition version for its whole life (`definition`); it is never changed after creation. Applications enforce this.
- The subject of an instance is a pair, `subject_entity_type` + `subject_entity_id`, with no relationship. Allowed subjects are in `config/edm-rules.yaml`.
- Steps, transitions, completions and events point to their parent (`process_definition`, `from_step`/`to_step`, `process_instance_id`); the parent does not list them.

Built by `migration/build.py` and awaiting Studio verification ([D12](../../../docs/decisions/0012-complete-without-studio.md)): open and save it in Studio before trusting it ([runbook](../../../docs/workflows/studio-verification.md)).
