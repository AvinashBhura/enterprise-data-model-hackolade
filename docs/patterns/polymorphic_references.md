# Pattern — References to More Than One Entity Type

## The principle

> When an attribute can point to more than one kind of entity, choose the
> narrowest shape that fits. Prefer typed references; use a polymorphic pair
> only at generic levels, and list every one in `config/edm-rules.yaml`.

## The "Party" alternative we rejected

In FIBO and ISO 20022, a `Party` abstract class sits over both Person and
Organization, and many references point to `Party`. We chose **not** to
introduce `Party`: it adds an abstraction business users don't recognise,
and a reference to "a Party" says less than a reference to "a Person". The
EDM uses Person + Organization + Role instead.

## Shape 1 — Typed references, one per type (preferred)

When an attribute can hold one of **two or three** known types, use one
typed reference per type, with a rule that exactly one is filled. Each is a
real relationship, so the database enforces it.

| Attribute | Points to | Rule |
|---|---|---|
| `Role.held_by_person` | Person | Exactly one of the two is filled |
| `Role.held_by_organization` | Organization | |

For roles where the ambiguity isn't real, make the one that applies
required. An `EmployeeRole` always has `held_by_person`; a `VisitorRole`
too.

## Shape 2 — Polymorphic pair (generic levels only)

When an attribute can point to **any of several** entity types and typed
references would multiply, use a pair:

| Attribute | Holds |
|---|---|
| `<name>_entity_type` | The entity type, from an `enum` of allowed types |
| `<name>_entity_id` | The `entity_id` of the record |

The pair has no relationship, so the database cannot check it. Two rules
make up for that:

1. Every pair is listed in `config/edm-rules.yaml` (`polymorphic_references`) with its allowed types.
2. `make check-references` fails on an unlisted pair, an `enum` value outside the allowed list, a missing `_entity_id`, or an allowed type that is not an entity in the EDM.

## Where the EDM uses polymorphic pairs

| Pair | Allowed types | Why |
|---|---|---|
| `Activity.participant_entity_type` (in `participants`) | Person, Organization, LegalEntity, OrganizationalUnit, Team, Role | Participants are genuinely diverse |
| `Activity.primary_actor_entity_type` | Same | Same |
| `Asset.custodian_entity_type` | Same | A Person, an organisation or a Team can hold an asset |
| `Role.engaging_party_entity_type` | Person, Organization, LegalEntity, OrganizationalUnit, Team | The other side of an engagement |
| `AgreementParty.party_entity_type` | Same | Agreements between any combination of parties |
| `StateTransition.transitioned_by_entity_type` | Person, Role, Team | Who made a state change |
| `ProcessInstance.subject_entity_type` | Domain entities a process runs on | The process subject (Borrower principle) |
| `transaction_hierarchy.transaction_entity` | Classifiable entities | The classified record ([D11](../decisions/0011-common-taxonomy-model.md)) |

## When not to use a pair

- One type dominates and the other is rare: use the dominant type and handle
  the edge case separately.
- The same pair appears in many places: an abstraction may be earning its
  place. Raise it with the EDM steering committee before adding more pairs.
- At Domain level, where the types are known: use typed references.

## Trade-offs

- **No database enforcement** for pairs: the application that writes the
  data must check the type and id.
- **Query complexity**: a query on a pair joins by type, often with one
  branch per type.
- **Documentation**: every pair's description says why each allowed type
  is valid.
