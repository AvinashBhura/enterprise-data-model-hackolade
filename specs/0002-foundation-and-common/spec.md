# 0002 — Foundation and Common models

Status: Implemented (2026-10-12), awaiting Studio verification
Owner: EDM architecture
Decisions: [D1](../../docs/decisions/0001-cross-file-specialisation.md), [D2](../../docs/decisions/0002-base-type-attributes-on-entities.md), [D3](../../docs/decisions/0003-enumerations-on-attributes.md), [D5](../../docs/decisions/0005-one-time-converter.md), [D11](../../docs/decisions/0011-common-taxonomy-model.md), [D12](../../docs/decisions/0012-complete-without-studio.md)
Depends on: 0001; Studio verification (D12) before Verified

## Problem

The Foundation and Common layers exist only as LinkML YAML. Every other layer
depends on them, so they move first. The move must keep every Foundation concept,
attribute, description and semantic mapping, while applying D2 (base-type
attributes on each entity), D3 (enums on attributes, no reference data) and D11
(one generic taxonomy model).

## Scope

In scope:
- `src/01_foundation/Foundation.hck.json` — the 11 Foundation concepts.
- `src/01_foundation/common/CommonValueTypes.hck.json` — shared composite value types.
- `src/01_foundation/common/CommonTaxonomy.hck.json` — the generic taxonomy model.
- Base-type contracts in `config/edm-rules.yaml`.
- The one-time converter in `migration/`, deleted when spec 0003 is Verified.

Out of scope:
- Domain, process and application models.
- Loading taxonomy data. The EDM stores schemas only.

## Requirements

### Converter (D5)

1. `migration/convert.py` reads the LinkML schemas from tag `linkml-final-v0.5.0` and writes `.hck.json` files in Hackolade's persistence schema 8 structure, with `dbVendor` and `appTarget` set to `Polyglot`.
2. It writes entities, attributes, data types, descriptions, required flags, `enum` lists, model definitions, external definitions and relationships. Every object gets a new GUID; `idToNameHashTable` lists every GUID.
3. It writes supertype groups only in the format captured by spike T1. If T1 has not captured it, the converter writes `migration/supertype-checklist.md` instead, and a modeller adds the groups in Studio.
4. LinkML descriptions become Hackolade descriptions, word for word. `class_uri` and `slot_uri` values (schema.org, SKOS) go into the `semanticUri` custom property.
5. Each converted file is opened and saved once in Studio before it is committed. The committed file is the one Studio saved, never the converter's raw output.
6. The converter never runs on a file that already exists in `src/`. It is for first creation only.

### Foundation model

7. `Foundation.hck.json` has the root `Entity` and one entity per Foundation concept: Person, Organization, LegalEntity, OrganizationalUnit, Team, Role, Activity, Agreement, Asset, Address, Document, Period. Every LinkML attribute is kept with its name, type, required flag and description.
8. Supertype groups:
   - `entity_id` (uuid, primary key) is declared directly on every Foundation concept, under an `Entity` contract in `config/edm-rules.yaml`. This keeps the key when one concept is derived into another model on its own.
   - `Entity` is kept as a **Polyglot only** entity documenting the root, so it is never derived as a table. It becomes the supertype of the 10 direct children (Person, Organization, Team, Role, Activity, Agreement, Asset, Address, Document, Period) only if spike T1 step 7 shows that this does not duplicate or remove `entity_id`.
   - `Organization` is the supertype of LegalEntity and OrganizationalUnit, as in LinkML (abstract supertype, total and disjoint).
9. `AgreementParty` stays a model definition inside the Foundation model, used by `Agreement.parties`.

### Base-type attributes (D2)

10. Each entity carries its base-type attributes directly, and lists the base types it follows in the `edmComposes` custom property. `config/edm-rules.yaml` holds each contract:

    | Base type | Attributes on the entity |
    | --- | --- |
    | Identifiable | `natural_identifiers` (array of NaturalIdentifier), `created_at`, `created_by`, `last_modified_at`, `last_modified_by` |
    | Lifecycleable | `lifecycle_state` (required, the entity's own `enum`), `state_effective_from`, `state_effective_to`, `state_history` (array of StateTransition) |
    | Temporal | `valid_from`, `valid_to`, `recorded_from`, `recorded_to` |
    | Addressable | `addresses`: array of `address_id` values, each a relationship to Address. The purpose (home, billing...) stays on `Address.address_type`, as in LinkML |
    | RoleHolder | No attribute. The entity is a valid target of `Role.held_by_person` or `Role.held_by_organization`. The LinkML `roles` list was the inverse of that relationship |
    | Classifiable | No attribute. The entity may be a target in `transaction_hierarchy` (resolved question 1) |

11. `check_base_types` (spec 0001) passes for every Foundation entity.

### Enumerations (D3)

12. Each LinkML lifecycle and type enum becomes an `enum` list on the attribute that uses it, in the entity that owns it. Value meanings go into the attribute's `valueDefinitions` custom property, as `VALUE: meaning` lines.
13. The ISO code lists become format rules, with the standard named in the attribute description. No values are stored:

    | Code list | Pattern | Standard |
    | --- | --- | --- |
    | Currency | `^[A-Z]{3}$` | ISO 4217 |
    | Country | `^[A-Z]{2}$` | ISO 3166-1 alpha-2 |
    | Language | `^[a-z]{2}$` | ISO 639-1 |
    | Unit of measure | `^[A-Z0-9]{2,3}$` | UN/CEFACT Recommendation 20 |
    | Time zone | `^[A-Za-z_]+(/[A-Za-z_0-9+\-]+)+$` (kept) | IANA time zone database |

### Polymorphic references

14. LinkML attributes whose range is `Entity` become a pair of attributes, `<name>_entity_type` and `<name>_entity_id`, with no relationship. This is the pattern `ProcessInstance` already uses. Affected: `Activity.participants` (an array of pairs plus `participation_role`), `Activity.primary_actor`, `Asset.custodian`, `Role.engaging_party`, `AgreementParty.party`, `StateTransition.transitioned_by`.
15. Allowed entity types for each pair are listed in `config/edm-rules.yaml`. `check_references` enforces them.

### Common value types

16. `CommonValueTypes.hck.json` holds these as model definitions: AmountType, QuantityType, DocumentType, StateTransition, NaturalIdentifier. Entities reuse them by external reference (D2 keeps composite value types shared).

### Common taxonomy model (D11)

17. `CommonTaxonomy.hck.json` holds five entities with the attributes approved in D11: `taxonomy`, `taxonomy_version`, `taxonomy_node`, `taxonomy_closure`, `transaction_hierarchy`. Business names are title case ("Taxonomy Version"); technical names come from the naming convention (snake_case).
18. Relationships: `taxonomy_version` → `taxonomy`; `taxonomy_node` → `taxonomy`; `taxonomy_node.parent_node_key` → `taxonomy_node.node_key`; `taxonomy_closure` ancestor and descendant → `taxonomy_node.node_key`; `transaction_hierarchy` → `taxonomy_node`, `taxonomy_version`, `taxonomy`.
19. `transaction_hierarchy` refers to the classified record by `transaction_entity` + `transaction_id`, with no relationship. Allowed entity names are in `config/edm-rules.yaml`.
20. Each entity's description states the consistency rules from D11 (only `parent_node_key` is edited; closure and paths are derived in the same transaction; published versions never change; `transaction_hierarchy` is append-only). These rules are enforced by the applications that write the data, not by the EDM.
21. The six LinkML taxonomy schemas are not converted. Their example hierarchies are copied into `docs/taxonomies-to-load.md` for the reference-data owners.

## Acceptance criteria

1. Every LinkML Foundation class and attribute appears in `Foundation.hck.json` with the same name and description, except the changes listed in requirements 10, 13 and 14. Checked by `migration/compare.py`, which lists every difference.
2. Studio opens all three files without errors or warnings. Checked by hand; screenshot attached to the pull request.
3. A trial derivation of Foundation to PostgreSQL (`polyglotDerive`, then `forwEng`) produces one table per concrete concept (11: Organization is abstract), no `entity` table, and `entity_id` on each table. Output attached to the pull request; not committed.
4. `make check` passes.
5. No `enum` lists any ISO code value. Checked by `check_enums` configuration.

## Validation

```bash
python migration/compare.py --tag linkml-final-v0.5.0
make check
hackolade polyglotDerive --target=PostgreSQL --polyglotmodels=src/01_foundation/Foundation.hck.json --targetmodel=/tmp/foundation-pg.hck.json
hackolade forwEng --model=/tmp/foundation-pg.hck.json --path=/tmp/foundation-ddl --outputType=script
```

## Resolved questions

Approved by Avinash Bhura on 2026-10-12 with the recommended answers.

1. Classifiable: option A. The `classifications` attribute is removed from the 8 Foundation entities. Classifiable becomes a marker with no attribute; an entity that lists it in `edmComposes` may be a target in `transaction_hierarchy`. A record's classification and its history live only in `transaction_hierarchy`.
2. Polymorphic references: the `<name>_entity_type` + `<name>_entity_id` pattern in requirement 14 is confirmed.

## Amendments — 2026-10-12, decision [D12](../../docs/decisions/0012-complete-without-studio.md)

No Hackolade licence is available, so the spikes could not run first. These changes apply; everything else stands.

1. **Converter (req 1–6).** The converter is `migration/build.py`, with `models.yaml`, `compare.py` and `validate_structure.py` (see `migration/README.md`). It reads the schemas from the tag with `git archive`. Files are written in the structure of Studio-saved files, checked against Hackolade's sample models, and marked `edmBuiltBy`. Requirement 5 (open and save in Studio) moves to `docs/workflows/studio-verification.md`, which must be done before this spec is Verified.
2. **Inheritance (req 3, 8).** No supertype groups are written. Each entity carries its Foundation kind's attributes (D12); LegalEntity and OrganizationalUnit carry Organization's. Entity and Organization are marked `edmAbstract`; the runbook sets Hackolade's *Polyglot only* flag on them.
3. **Names (req 7, 17).** Entity business names are PascalCase, as the naming rule requires: `LegalEntity`, `OrganizationalUnit`, `TaxonomyVersion`, `TaxonomyNode`, `TaxonomyClosure`, `TransactionHierarchy`. Technical names stay snake_case.
4. **AgreementParty (req 9).** Written inline as the item structure of `Agreement.parties`: no public Polyglot sample uses model definitions. Its `party` is a pair; `signed_by_person` is an id with no relationship (nested).
5. **Value types (req 16).** AmountType, QuantityType, DocumentType, StateTransition and NaturalIdentifier are entities in `CommonValueTypes`, marked `edmValueType`, reused by entity-level external reference (the pattern of Hackolade's `common/Address` sample).
6. **Organization references (req 14).** Organization is abstract, so references to it become pairs with allowed types LegalEntity and OrganizationalUnit, listed in `config/edm-rules.yaml`. Two keep a relationship to a concrete subtype because their name says which: `EmployeeRole.employing_legal_entity` → LegalEntity, `Position.organizational_unit` → OrganizationalUnit.
7. **Inherited self-references.** `Document.replaces_document`, `Period.parent_period` and `Team.parent_team` point to the specialising entity itself (a JobRequisition replaces a JobRequisition). Other inherited references keep their Foundation target.
8. **Enum change (D3, justified).** `Role.role_type` gains `CANDIDATE` (Candidate is a Role held by a Person) and `INTERVIEWER` (InterviewPanelAssignment is the interviewer role an employee holds for one interview). No value is removed.
9. **Base types (req 10).** The `lifecycle_state` contract accepts `enum` or `string`: Document and Period had no lifecycle list at the tag; their specialisations each set one. The `addresses` contract text is the original description, word for word.
10. **Format rules (req 13).** `Address.timezone` takes the IANA time-zone pattern.
11. **Descriptions (req 4).** Seven descriptions that described schema-language mechanics ("narrows the range", "union range", "generator rules", "mixin") are reworded with the same meaning; `migration/models.yaml` lists them and `compare.py` reports each one.
12. **Taxonomy (req 18).** `parent_node_key`, `ancestor_node_key` and `descendant_node_key` refer to `TaxonomyNode.node_key`, which repeats across version rows. The relationships are logical; a physical model of the taxonomy enforces them in the application or adds a node-identity table, decided in the spec that first derives it.
13. **Acceptance criteria 2 and 3** are checked during Studio verification. Criterion 1: `python migration/compare.py --scope foundation` and `--scope common` show every difference explained.
