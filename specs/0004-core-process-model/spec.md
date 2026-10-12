# 0004 — Core process model

Status: Implemented (2026-10-12), awaiting Studio verification
Owner: EDM architecture
Decisions: [D1](../../docs/decisions/0001-cross-file-specialisation.md), [D2](../../docs/decisions/0002-base-type-attributes-on-entities.md), [D3](../../docs/decisions/0003-enumerations-on-attributes.md), [D6](../../docs/decisions/0006-migration-scope.md), [D12](../../docs/decisions/0012-complete-without-studio.md)
Depends on: 0002 Implemented; Studio verification (D12) before Verified

## Problem

The Process layer separates workflow state from entity state. Its six core
entities exist only in LinkML. They must move to Hackolade without any sample
business process (brief, section 8).

## Scope

In scope:
- `src/03_process/_core/CoreProcess.hck.json` with the six core entities and their enums.

Out of scope:
- The seven LinkML sample processes (removed, listed in the migration backlog).
- Any business-specific process definition. Process definitions are data, created by applications.

## Requirements

1. The model has these entities, migrated with all LinkML attributes and descriptions:

   | Entity | Foundation kind | Purpose |
   | --- | --- | --- |
   | ProcessDefinition | Document | A versioned definition of a process |
   | ProcessStep | Activity | A step in a definition |
   | ProcessTransition | Document | An allowed move between two steps, with its condition |
   | ProcessInstance | Activity | One run of a definition, bound to one definition version for its whole life |
   | StepCompletion | Activity | The record of one step completed in one instance |
   | ProcessEvent | Activity | An event raised during an instance |

2. Enums move onto their attributes (D3): `ProcessDefinitionStateEnum` on `ProcessDefinition.lifecycle_state`, `ProcessInstanceStateEnum` on `ProcessInstance.lifecycle_state`, `StepOutcomeEnum` on `StepCompletion.outcome`, `ProcessEventTypeEnum` on `ProcessEvent.event_type`.
3. Foundation kinds are applied as in spec 0003 (derive the needed Foundation entities, local supertype groups, roll-down), unless spike T2 changes the approach.
4. Relationships:
   - ProcessStep → ProcessDefinition (a step belongs to one definition version).
   - ProcessTransition `from_step` and `to_step` → ProcessStep.
   - ProcessInstance → ProcessDefinition, required and never changed after creation (binding immutability).
   - StepCompletion → ProcessInstance and → ProcessStep.
   - ProcessEvent → ProcessInstance; `related_step` → ProcessStep.
   - ProcessInstance `migrated_to_instance` and `migrated_from_instance` → ProcessInstance.
   - ProcessDefinition `replaces_definition` → ProcessDefinition.
5. The process subject stays a typed pair: `subject_entity_type` + `subject_entity_id`, no relationship. Allowed subject types are listed in `config/edm-rules.yaml` and checked by `check_references`.
6. The LinkML arrays `ProcessDefinition.steps`, `ProcessDefinition.transitions`, `ProcessInstance.step_completions` and `ProcessInstance.events` were inverses of the relationships above. They become relationships, not stored arrays.
7. `implements_capability` stays a string, with its description noting it should name a capability from the business capability model when one exists.
8. Binding immutability is stated in the ProcessInstance description and in the `definition` attribute description. It is enforced by applications, not by the schema.

## Acceptance criteria

1. The model has exactly six entities and no business-specific process. Checked by review and `check_metadata`.
2. `migration/compare.py --scope process-core` shows no unexplained difference.
3. A trial derivation to PostgreSQL gives six tables with the foreign keys in requirement 4. Output attached to the pull request.
4. `make check` passes and Studio opens the model without errors.

## Validation

```bash
python migration/compare.py --tag linkml-final-v0.5.0 --scope process-core
make check
```

## Open questions

None.

## Amendments — 2026-10-12, decision [D12](../../docs/decisions/0012-complete-without-studio.md)

1. **Requirement 3.** Entities carry their Foundation kind's attributes (D12); CoreProcess derives Person and Role from the Foundation as relationship targets.
2. **Requirement 4.** ProcessStep gains `process_definition` (required, → ProcessDefinition), the relationship that replaces `ProcessDefinition.steps`. `StepCompletion.process_instance_id` and `ProcessEvent.process_instance_id` become relationships to ProcessInstance.
3. **Requirement 5.** `subject_entity_type` and `subject_entity_id` stay text, as at the tag; the allowed subject (`JobApplication`) is listed in `config/edm-rules.yaml`.
4. **ProcessDefinition.applies_to_organization** becomes a pair (spec 0002 amendment 6).
5. **Acceptance criterion 3** (trial derivation) is checked during Studio verification.
