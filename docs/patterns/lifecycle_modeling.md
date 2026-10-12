# Pattern — Lifecycle Modeling

## The principle

> Lifecycle is a **base type** (`Lifecycleable`) entities opt into. The
> specific lifecycle state enum is **per-entity**. Coarse entity
> lifecycle is distinct from fine workflow state.

## The two scales of state

The EDM tracks state at two scales:

| Scale | Where it lives | Example |
|---|---|---|
| **Entity-level lifecycle** | `Lifecycleable.lifecycle_state` on the entity | `EmployeeRole.lifecycle_state = ACTIVE` |
| **Workflow state** | `ProcessInstance.lifecycle_state` and its `StepCompletion` records | An onboarding instance that has completed its access-provisioning step |

Don't conflate them. An employee being ACTIVE (entity lifecycle) is
different from her onboarding having reached access provisioning (workflow state).

## Entity-level lifecycle pattern

An entity that has a lifecycle lists `Lifecycleable` in its `edmComposes`
custom property and declares the base type's attributes itself, exactly as
the contract in `config/edm-rules.yaml` says ([D2](../decisions/0002-base-type-attributes-on-entities.md)):

| Attribute | Type | Required |
|---|---|---|
| `lifecycle_state` | `enum` — the entity's own values | Yes |
| `state_effective_from` | datetime | No |
| `state_effective_to` | datetime | No |
| `state_history` | array of `StateTransition` | No |

For `EmployeeRole`, the `enum` on `lifecycle_state` holds the employment
states (OFFER_EXTENDED, ACTIVE, ON_LEAVE, SEPARATED, ...), with their
meanings in `valueDefinitions` ([D3](../decisions/0003-enumerations-on-attributes.md)). `make check-base-types`
verifies every entity against the contract.

## The "one enum per entity" decision

We chose **one lifecycle enum per entity** rather than a few shared
enums for two reasons:

1. **Semantic precision** — Person's lifecycle (PROSPECT → ACTIVE → MERGED)
   is genuinely different from Agreement's (DRAFT → SIGNED → EXECUTED →
   TERMINATED). Forcing them to share an enum forces awkward middle
   ground.
2. **Independent evolution** — adding a new state to one entity (say,
   adding `RECONSIDERATION` to Offer) shouldn't affect every other
   entity that happens to share the enum.

## State transitions are append-only

`state_history` is an immutable list of `StateTransition` records.
Each transition records `from_state`, `to_state`, timestamp, actor, and
reason. Never edit a past transition; always append a new one when state
changes.

`StateTransition` is a value type in Common:

| Attribute | Type | Required |
|---|---|---|
| `from_state` | string | Yes |
| `to_state` | string | Yes |
| `transition_timestamp` | datetime | Yes |
| `transitioned_by_entity_type` + `transitioned_by_entity_id` | polymorphic pair (Person, Role or Team) | No |
| `reason` | string | No |

This gives you point-in-time reconstruction: "what state was this
entity in on July 17?" is answerable by walking the state_history.

## What about workflow state?

Workflow state lives on the ProcessInstance, not on the entity.
- `ProcessInstance.lifecycle_state` — generic instance state
  (IN_PROGRESS, COMPLETED, ...).
- `StepCompletion` records — which steps of the bound definition are done,
  by whom, with what outcome.

Both describe the run of a process, never the entity it runs on.

## Why entities don't carry workflow state

Putting workflow state on entities is a common error. It feels
convenient ("just add `current_workflow_step` to Employee") but it
breaks the architecture:

- Domain becomes bloated with fields only relevant to specific processes
- A single entity can't be in multiple processes simultaneously
- Process changes force Domain schema changes (volatility leak)

Keep workflow state on `ProcessInstance`. The entity carries only
its coarse lifecycle.
