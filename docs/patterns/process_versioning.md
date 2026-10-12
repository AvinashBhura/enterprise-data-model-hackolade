# Pattern — Process Versioning

## The principle

> Every `ProcessDefinition` carries a **version**. `ProcessInstance`
> binds to a specific definition version at creation, **immutably**,
> for its entire lifetime.

## Why versioning is essential

Business processes change constantly. Without versioning:
- Running instances behave inconsistently when the definition changes
  mid-flight.
- Audit trails become irreproducible — "what process was running on
  this instance on June 5?" can't be answered.
- Rollback is impossible.

With versioning, each instance is a self-contained, reproducible
record bound to a specific definition snapshot.

## Versioning shape

| Entity | Attribute | Rule |
|---|---|---|
| ProcessDefinition | `definition_name` | Required, e.g. "Employee Onboarding" |
| ProcessDefinition | `version` | Required; a SemVer string, e.g. "3.2.0" |
| ProcessDefinition | `lifecycle_state` | `enum`: DRAFT, PUBLISHED, DEPRECATED, RETIRED |
| ProcessDefinition | `replaces_definition` | Relationship to the predecessor definition |
| ProcessInstance | `definition` | Relationship to ProcessDefinition; required; **never changed** |

## SemVer rules for ProcessDefinitions

- **Major version** (3.x → 4.x) — breaking change to step set or
  transitions; existing instances should NOT migrate automatically.
- **Minor version** (3.2 → 3.3) — additive change (new step, new
  optional field); existing instances may continue to run.
- **Patch version** (3.2.0 → 3.2.1) — bugfix or non-functional change
  (description text, sequence-number reordering); existing instances
  unaffected.

## The Frozen-Contract rule (Operational Rule 4)

> A ProcessInstance's binding to a ProcessDefinition is set at
> creation and **NEVER** changes. Process migrations are modeled as
> *termination of the old instance + creation of a new instance with
> explicitly carried-over state*, never as mutation of the binding.

This is the most important versioning rule. Mutating an instance's
`definition` reference would make audit trails irreproducible.

## Migration workflow

When you need to migrate Priya's onboarding from v3.2 to v4.0:

1. **Set old instance to MIGRATED state.** Update `state_history` and
   set `migrated_to_instance` to the new instance's entity_id. Do NOT
   change the `definition` reference on the old instance.
2. **Create new instance bound to v4.0.** Set its `migrated_from_instance`
   to the old instance's entity_id.
3. **Carry over state.** Copy completed steps from old to new (as
   `StepCompletion` records associated with the equivalent v4.0 steps).
   Document the mapping explicitly.
4. **Emit ProcessEvent.** Both instances get an `INSTANCE_MIGRATED`
   event recording the timestamp and reason.

Illustrative data for the two instances:

```yaml
# Old instance — set to MIGRATED, definition pointer unchanged
old_instance:
  definition: pdef_onboarding_us_eng_v3_2   # UNCHANGED
  lifecycle_state: MIGRATED
  migrated_to_instance: new_instance.entity_id

# New instance — bound to v4.0
new_instance:
  definition: pdef_onboarding_us_eng_v4_0
  lifecycle_state: IN_PROGRESS
  migrated_from_instance: old_instance.entity_id
  # ... carry-over StepCompletions
```

## Versioning trade-offs

**Pro:** full audit trail, reproducibility, safe parallel evolution.
**Pro:** A/B testing of process variants.
**Con:** more instance proliferation when migrations happen.
**Con:** runtime needs to dereference `definition` correctly (cache!).

The pros far outweigh the cons in regulated environments and any
audit-sensitive context.

## When to bump major vs minor

| Change | Version bump |
|---|---|
| Add a new optional step at the end | Minor |
| Add a new required step in the middle | Major |
| Rename a step | Patch (if semantically same) or Major (if semantics changed) |
| Reorder steps without changing dependencies | Patch |
| Change the responsible role for a step | Major (changes authority semantics) |
| Add a new state to an enum | Minor (most consumers handle gracefully) |
| Remove a state from an enum | Major (breaking) |
