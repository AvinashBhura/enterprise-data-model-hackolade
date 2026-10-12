# Domain layer

**Owner:** each domain's steward. **May depend on:** Foundation, Common, and other Domain models (no cycles).

One polyglot model per subdomain (bounded context), in `<Domain>/<Subdomain>/<Subdomain>.hck.json`. Each entity is defined in exactly one model; other models reuse it by derivation (a read-only copy) or external reference (`make check-ownership`).

| Domain | Status |
| --- | --- |
| [HR](HR/README.md) | Six subdomain models: [spec 0003](../../specs/0003-hr-and-talent-acquisition/spec.md), awaiting Studio verification |
| Others | Frozen; see [docs/migration-backlog.md](../../docs/migration-backlog.md) |

Domain entities specialise exactly one Foundation kind and carry its attributes (`make check-foundation-kind`, `make check-foundation-contract`).
