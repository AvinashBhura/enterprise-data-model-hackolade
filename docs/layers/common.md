# Layman's Guide — Common Sub-Layer

## What it is in one sentence

The shared building blocks — value types and the taxonomy model — that
every layer above uses to construct its entities.

## Why it matters

Suppose every department that records a money amount invents its own
way: HR stores it as a number with a separate currency field, Finance
as a string like "$1,200.00 USD", Sales as an object with nested
values. Now build a report that sums them all. You can't, without
heroic translation.

Common says: **we all use the same definitions for shared things.**
A money amount is *always* `value + currency`. A country is *always*
identified by an ISO code.

## What lives here

### Value types (`CommonValueTypes.hck.json`)

Composite values with no identity of their own, reused by external
reference wherever they appear: `AmountType` (value + currency),
`QuantityType` (value + unit of measure), `DocumentType`,
`StateTransition`, `NaturalIdentifier`. Each is an entity marked as a value
type: it never becomes a table on its own, only the structure of the
attribute that uses it ([D12](../decisions/0012-complete-without-studio.md)).

### The taxonomy model (`CommonTaxonomy.hck.json`)

One generic model that stores **every** enterprise taxonomy as data —
organisation types, position types, geography, industry, chart of
accounts — with unlimited depth and full version history: `taxonomy`,
`taxonomy_version`, `taxonomy_node`, `taxonomy_closure`,
`transaction_hierarchy`. See
[D11](../decisions/0011-common-taxonomy-model.md).

## What no longer lives here, and where it went

| Before | Now | Decision |
|---|---|---|
| Base types as mixins (`Identifiable`, `Lifecycleable`, ...) | Attributes declared on each entity; one contract per base type in `config/edm-rules.yaml` | [D2](../decisions/0002-base-type-attributes-on-entities.md) |
| Lifecycle and type enums | An `enum` on the attribute of the entity that owns it | [D3](../decisions/0003-enumerations-on-attributes.md) |
| ISO code lists (currency, country, language, unit) | A format rule on the attribute; the values are reference data, kept outside the EDM | [D3](../decisions/0003-enumerations-on-attributes.md) |
| One schema per taxonomy | Rows in the taxonomy model | [D11](../decisions/0011-common-taxonomy-model.md) |

The EDM is a schema store: it holds the rules for values, never the values.

## Why Common sits *under* Foundation, not as a peer

Common is construction material — it's not an enterprise concept in
its own right. "A currency code" is not a thing your business *does*
or *has*; it's a way of *describing* things your business has. That's
why Common is nested under Foundation, and why it depends on nothing.

## The Reusability Test

Before placing anything in Common, ask:
*Would another enterprise, with a completely different business, still
need this exact construct?*
- Yes → Common-worthy.
- No → it belongs in Domain, or it is data, not schema.

## See also

- Common principles: [principles.md](../architecture/principles.md) (Common section)
- Schema vs reference data: [operational_rules.md](../architecture/operational_rules.md) (Rule 5)
