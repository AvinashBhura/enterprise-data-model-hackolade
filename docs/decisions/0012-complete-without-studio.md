# D12 — Complete the models before Hackolade Studio is available

Status: Proposed — implemented as an interim; confirm or reject after the Studio runbook
Date: 2026-10-12
Replaces in part: [D1](0001-cross-file-specialisation.md) (until spike T1 passes)

## Context

Specs 0002–0005 assumed spikes T1–T5 would run first. They cannot: no
Hackolade licence is available yet, and the user asked for every spec to be
completed now, with Studio verification at the end.

Three things the specs relied on are not shown in any public Hackolade file:

1. How a **supertype group** is stored. D1 needs one per Foundation kind in
   every domain model.
2. How an attribute references a **model definition**, in its own model or
   another one. No public Polyglot sample uses model definitions.
3. What `polyglotDerive` writes for a **PostgreSQL** target.

Hackolade's public sample models (`hackolade/demo-models-read-only`, saved by
Studio 8.0–8.11) do show: entities, attributes, enums, relationships,
entity-level external references (`common/Customer` reusing
`common/Address`), polyglot derivation of entities between polyglot models
(`ecommerce/Order management-Polyglot`), derived physical models
(`Pragmatic data modeling/*-Oracle`) and native PostgreSQL models
(`PostgreSQL/DVDrental`). The PostgreSQL plugin source (`hackolade/PostgreSQL`)
shows its column types, keys and indexes.

## Decision

1. **Inheritance (interim form of D1).** Each Domain, Process and Application
   entity carries the attributes of its Foundation kind, exactly as
   `Foundation.hck.json` defines them, plus its own. `foundationKind` names
   the kind. This is the shape D1's roll-down strategy produces.
   `check_foundation_contract` verifies every such entity against the
   Foundation model, allowing only the narrowing listed in
   `config/edm-rules.yaml` (required may be tightened; listed enums may be
   narrowed, replaced or closed from free text). Inside the Foundation,
   LegalEntity and OrganizationalUnit carry Organization's attributes the
   same way.
2. **Reuse across models** uses only patterns seen in Hackolade's samples:
   - an entity owned by another model is **derived** into the model that
     needs it (read-only copy, `refType: polyglot`), and relationships point
     to the derived copy;
   - value types (AmountType, QuantityType, DocumentType, StateTransition,
     NaturalIdentifier) are **entities** in `CommonValueTypes.hck.json`,
     reused by entity-level **external reference**, as Hackolade's
     `common/Address` sample is. They are marked `edmValueType` and are
     never tables on their own;
   - AgreementParty, which was a separate class used only by
     `Agreement.parties`, is written inline as the structure of that array.
3. **Model files are written by the one-time builder** in `migration/`, in
   the structure of Hackolade's saved files (persistence schema 8), and checked
   against the samples by `migration/validate_structure.py`. They have not been
   opened in Studio. They carry the model property `edmBuiltBy`, and
   `check_format` accepts them while `format.accept_builder_output` is true.
   Every spec stays "Implemented, awaiting Studio verification" until
   `docs/workflows/studio-verification.md` is done.
4. **The Candidate Journey physical model** is written in the structure of a
   derived physical model, with PostgreSQL types taken from the PostgreSQL
   plugin and its samples. Arrays and composite value types are `jsonb`
   columns (derivation without normalisation). Its physical design is also
   listed in its README, so it can be re-applied if Studio's own derivation
   is preferred.
5. **Entities that must never become tables** (Entity, Organization) carry
   `edmAbstract`; the runbook sets Hackolade's *Polyglot only* flag on them,
   because its stored form is not public either. References to Organization
   are polymorphic pairs restricted to LegalEntity and OrganizationalUnit.

## Consequences

- Same tables as D1 with roll-down, available now, checkable now.
- Foundation attributes are repeated on every specialising entity. A
  Foundation change means editing those entities; `make check` lists every
  one that no longer matches. This is the trade-off already accepted for
  base types in [D2](0002-base-type-attributes-on-entities.md).
- Hackolade's diagram does not show inheritance until supertype groups are
  added.
- If spike T1 passes, a follow-up spec can add supertype groups and remove
  the copied attributes. If it fails, this decision becomes the permanent
  form of D1.
- If Studio rejects any written file, the runbook falls back to building
  that model in Studio from its README and spec.
