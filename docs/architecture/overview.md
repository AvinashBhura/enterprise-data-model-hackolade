# Architecture Overview

The Enterprise Data Model is built in **five layers**, stacked from
most stable (bottom) to most volatile (top), with dependencies flowing
**upward only**.

## The Five Layers

```
┌─────────────────────────────────────────────────────────────┐
│ 5. APPLICATION    system-specific projections                │
├─────────────────────────────────────────────────────────────┤
│ 4. PROCESS        workflows and instances                    │
├─────────────────────────────────────────────────────────────┤
│ 3. DOMAIN         capability-aligned stable nouns            │
├─────────────────────────────────────────────────────────────┤
│ 2. COMMON         shared construction material               │
│   (nested inside Foundation)                                 │
├─────────────────────────────────────────────────────────────┤
│ 1. FOUNDATION     permanent enterprise concepts              │
└─────────────────────────────────────────────────────────────┘
```

### Foundation Layer
The permanent, universal concepts that define what an enterprise is —
people, organizations, teams, activities, roles, agreements, assets,
addresses. Rarely changes. Every higher layer extends or references
these.

### Common Sub-Layer (nested under Foundation)
The shared toolkit — value types and the generic taxonomy model —
that every layer above uses to construct its specifics. Not enterprise
concepts in their own right; they are the *material* used to build
real things.

### Domain Layer
Capability-aligned specializations — what each business function
(HR, Finance, Sales, Procurement, Legal, Security, IT, Facilities,
Governance) actually works with. Stable nouns; never workflows.

### Process Layer
The workflows, steps, transitions, and events that describe how
capabilities are executed. Versioned and immutably bound, so workflow
churn doesn't disturb the stable layers below.

### Application Layer
Physical models of individual applications, with vendor identifiers
and quirks. When
a vendor system migrates (e.g., switching HRIS), only this layer
changes; everything below stays stable.

## The Golden Rule

**Dependencies flow upward only.**
Foundation knows nothing of Domain. Domain doesn't know about Process.
Nothing depends on Application. This is enforced by
`tools/check_layers.py` and is what makes evolution
possible — each layer can change at its own pace without breaking
others.

## Why This Layering Works

- **Volatility containment** — fast-changing things live high; slow-
  changing things live low. Volatility cannot leak downward because
  dependencies don't go that way.
- **Stewardship clarity** — each capability owns its piece of Domain;
  vendor teams own pieces of Application; architects govern Foundation.
- **Vendor independence** — Domain stays vendor-neutral because vendor
  fields live exclusively in Application.
- **Process flexibility** — process changes (frequent) ripple in
  Process layer only.
- **Audit and reproducibility** — Process events and Frozen-Contract
  binding give point-in-time reconstructability.

## Where to Go Next

- [`principles.md`](principles.md) — all 27 principles with mnemonic captions
- [`operational_rules.md`](operational_rules.md) — the five enforceable rules
- [`../layers/foundation.md`](../layers/foundation.md) — layman's guide to Foundation
