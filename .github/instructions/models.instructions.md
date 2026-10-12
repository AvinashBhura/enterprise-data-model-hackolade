---
applyTo: "src/**"
---

# Model files

- `.hck.json` files are Hackolade models. Do not edit them by hand or generate
  edits to them. Describe the change for a modeller to make in Studio: model,
  entity, attribute, property, value.
- A model may depend only on models in its own or a lower layer
  (Common < Foundation < Domain < Process < Application), with no cycles.
- Every Domain, Process and Application entity has `foundationKind`,
  `entityType`, `steward` and a description, and carries its Foundation kind's
  attributes.
- Enums sit on the owning attribute, with meanings in `valueDefinitions`. No
  reference data in the EDM.
- References to an entity owned by another model go through derivation.
  References that may point to several entity types are pairs
  `<name>_entity_type` + `<name>_entity_id`, listed in `config/edm-rules.yaml`.
- Each model folder has a README listing its entities; keep it in step.
