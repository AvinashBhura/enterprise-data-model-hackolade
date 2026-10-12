# The Dependency Direction Rule (One-Way Gate)

The single most important rule in the EDM:

> **Dependencies point down only.**
> Common ← Foundation ← Domain ← Process ← Application
> A model may depend on models in its own layer or any lower layer, never a higher one.

## What counts as a dependency

A Hackolade model depends on another model file in two ways:

| Dependency | How Hackolade stores it | Example |
|---|---|---|
| **Derivation** | The parent model's path in `polyglotModelPaths` | Candidate Journey (Application) is derived from Talent Acquisition (Domain) |
| **External reference** | The source file's path in each external definition's `link` | Talent Acquisition references `Position` from Workforce Planning |

Both count. A model's layer is the layer folder it sits in.

## Allowed dependencies

| Layer | Folder | May depend on |
|---|---|---|
| Common | `src/01_foundation/common/` | Itself only |
| Foundation | `src/01_foundation/` | Common |
| Domain | `src/02_domain/` | Common, Foundation, other Domain models |
| Process | `src/03_process/` | Common, Foundation, Domain |
| Application | `src/04_application/` | Every layer below |

A `_shared` folder belongs to the layer that contains it.

Within a layer, any model may depend on any other, as long as no cycle forms
(`make check-cycles`). For example, Talent Acquisition references
`EmployeeRole` from Core HR; Core HR must then not reference anything in
Talent Acquisition.

## Why it matters

This rule is what gives the EDM its **stability gradient**. Foundation
changes are rare and ripple everywhere; Application changes are constant
and ripple nowhere. The one-way arrows are what make this asymmetry
possible.

If even one upward dependency is allowed, the gradient collapses:
Foundation must change every time anything above it changes.

## How it's enforced

`tools/check_layers.py` reads every model file in `src/`, finds each
derivation and external-reference link, works out the layer of the target
file, and fails on any dependency that points to a higher layer, to a
missing file, or outside the layer folders. `tools/check_cycles.py` fails
on any cycle, direct or transitive.

Both run in `make check`, locally and in CI on every pull request.

## Common violations and fixes

**Violation:** a Foundation model references an entity in `02_domain/HR/`.
**Fix:** reverse the relationship. The Domain model references the
Foundation entity, not the other way.

**Violation:** a Domain model references a table in `04_application/Workday/`.
**Fix:** move the attribute up to Domain (if vendor-neutral) or drop it (if
Workday-specific). Application models depend on Domain; Domain never depends
on Application.

**Violation:** two subdomain models reference each other.
**Fix:** decide which subdomain owns the shared concept. The other references
it; the owner does not reference back.
