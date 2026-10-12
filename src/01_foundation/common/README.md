# Common sub-layer

**Owner:** EDM architecture. **May depend on:** nothing (lowest layer). Spec: [0002](../../../specs/0002-foundation-and-common/spec.md).

No reference data lives here: the EDM stores schemas only ([D3](../../../docs/decisions/0003-enumerations-on-attributes.md)).

## CommonValueTypes.hck.json

Composite value types, reused by entity-level external reference ([D2](../../../docs/decisions/0002-base-type-attributes-on-entities.md), [D12](../../../docs/decisions/0012-complete-without-studio.md)). Each is marked `edmValueType`: it is never a table on its own; it becomes the structure of the attribute that uses it.

| Entity | Foundation kind | Type | Description |
| --- | --- | --- | --- |
| AmountType | none | Supporting | A monetary amount: a decimal numeric value with its ISO 4217 currency code. |
| QuantityType | none | Supporting | A quantity: a numeric value with its unit of measure. |
| DocumentType | none | Supporting | A reference to a document stored in an external document management system (SharePoint, Google Drive, DocuSign, etc.). |
| StateTransition | none | Supporting | A single transition from one lifecycle state to another. |
| NaturalIdentifier | none | Supporting | A natural/business identifier value paired with the scheme that issued it and the issuer. |

Code lists are format rules, not values: currency `^[A-Z]{3}$` (ISO 4217), country `^[A-Z]{2}$` (ISO 3166-1 alpha-2), language `^[a-z]{2}$` (ISO 639-1), unit of measure `^[A-Z0-9]{2,3}$` (UN/CEFACT Rec. 20).

## CommonTaxonomy.hck.json

The generic, versioned taxonomy model ([D11](../../../docs/decisions/0011-common-taxonomy-model.md)). Every enterprise taxonomy is data in these entities; the six old taxonomies are listed in [docs/taxonomies-to-load.md](../../../docs/taxonomies-to-load.md).

| Entity | Foundation kind | Type | Description |
| --- | --- | --- | --- |
| Taxonomy | none | Core | One enterprise taxonomy, such as Position Type, Geography, Industry Classification or Chart of Accounts. |
| TaxonomyVersion | none | Supporting | A named release of a taxonomy: DRAFT, PUBLISHED or RETIRED. |
| TaxonomyNode | none | Core | One version row of a taxonomy node (adjacency list, materialised path and SCD Type 2). |
| TaxonomyClosure | none | Supporting | Every ancestor-descendant pair of nodes with its depth (closure table, SCD Type 2). |
| TransactionHierarchy | none | Supporting | Immutable history of which taxonomy node a business record was classified under, with the node version and both paths as they stood then. |

Rules that keep it consistent are enforced by the applications that write the data, not by the EDM: only `parent_node_key` is edited; closure rows and paths are derived in the same transaction; published versions never change; `TransactionHierarchy` is append-only.

Known limit: `parent_node_key`, `ancestor_node_key` and `descendant_node_key` refer to `TaxonomyNode.node_key`, which repeats across a node's version rows. The relationships are logical. A physical model of this schema enforces them in the application or adds a node-identity table; that choice is made in the spec that first derives it.

Built by `migration/build.py` and awaiting Studio verification ([D12](../../../docs/decisions/0012-complete-without-studio.md)): open and save it in Studio before trusting it ([runbook](../../../docs/workflows/studio-verification.md)).
