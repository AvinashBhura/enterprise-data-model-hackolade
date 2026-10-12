---
name: edm-modelling-rules
description: The EDM's modelling rules in one place - layers, Foundation kinds, base types, enums, references, junctions, derived models and naming - with the check that enforces each. Use when designing or reviewing any entity or attribute.
---

# EDM modelling rules

Each rule names the check that enforces it (`make check-<name>`) and where it is configured (`config/edm-rules.yaml`).

## Layers
- Common < Foundation < Domain < Process < Application. A model depends only on its own or a lower layer, with no cycles. (`layers`, `cycles`)
- Folder decides the layer; model property `edmLayer` must match. (`metadata`)

## Entities
- Required custom properties: `layer`, `foundationKind`, `entityType` (Core, Supporting, Bridge/Junction), `steward`, and a description. (`metadata`)
- Every Domain, Process and Application entity specialises exactly one Foundation kind and carries its attributes unchanged, except: `required` may be tightened; `lifecycle_state` gets the entity's own enum; `role_type`, `agreement_type`, `activity_type`, `organization_type` may be narrowed to a subset; `outcome` may be closed to an enum. (`foundation-kind`, `foundation-contract`)
- Technical entities in `src/04_application/_shared/` use `foundationKind: none`.
- Each entity is defined in one model; others derive it. (`ownership`)
- Entity and Organization are never tables (`edmAbstract`).

## Attributes
- Base types listed in `edmComposes` (Entity, Identifiable, Lifecycleable, Temporal, Addressable, RoleHolder, Classifiable) bring their contract's attributes with the same names, types and required flags. (`base-types`)
- Closed lists are `enum` lists on the owning attribute; meanings in `valueDefinitions` as `VALUE: meaning` lines. The same attribute name carries the same values everywhere unless listed in `enums.intended_differences`. (`enums`)
- ISO code lists are patterns, not values: currency `^[A-Z]{3}$`, country `^[A-Z]{2}$`, language `^[a-z]{2}$`, unit `^[A-Z0-9]{2,3}$`.
- Composite values (AmountType, QuantityType, DocumentType, StateTransition, NaturalIdentifier) are external references to `CommonValueTypes`.
- A reference to one entity type is a relationship to its `entity_id`. A reference that may point to several types is a pair `<name>_entity_type` + `<name>_entity_id`, listed in `polymorphic_references`. (`references`)
- Business names: entities PascalCase, attributes snake_case; technical names snake_case, at most 63 characters, no PostgreSQL reserved word. (`naming`)
- Personal data carries `dataClassification` (PII, Sensitive PII, Internal).

## Junctions
- A Bridge/Junction entity names the two entities it connects in `edmConnects`, has a relationship to each, and has its own key. (`junctions`)

## Derived and physical models
- Derived Foundation and Common entities are never changed locally, except a physical data type in a physical model; every other deviation has a `deviationReason`. (`deviations`)
- Files: persistence schema 8, saved by Studio 8.13+ (builder output accepted until Studio verification, D12). (`format`)

## Never
- Workflow state on Domain entities. Reference data in the EDM. Hand edits to `.hck.json`.
