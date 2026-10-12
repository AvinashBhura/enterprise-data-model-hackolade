# Layman's Guide — Domain Layer

## What it is in one sentence

The stable nouns each business capability operates on — extending
Foundation entities with the specifics each function needs.

## Why it matters

Foundation says "a Person." HR needs more: this Person has a hire
date, a position, a manager, a pay grade. Sales needs different
specifics: this Person is a contact at a customer account. Both are
still the same Person — but each capability needs to attach its own
information.

Domain lets each capability extend Foundation cleanly: HR adds
`EmployeeRole`; Sales adds `CustomerContactRole`; Procurement adds
`VendorRole`. Same Person underneath; different roles reflecting
different engagements.

## The Nine Capabilities

| Capability | What It Owns |
|---|---|
| **HumanResources** | Employment Roles, Positions, OnboardingChecklists, Compensation, EmploymentContracts, Performance Reviews |
| **Finance** | GL Accounts, Cost Centers, Budgets, Fiscal Periods, Journal Entries, Invoices, Payments |
| **Sales** | Customer Accounts, Opportunities, Quotes, Orders, OrderLines, CustomerContactRoles |
| **Procurement** | Vendor Roles, Vendor Contracts, Purchase Orders, Purchase Requisitions |
| **Legal** | NDAs, Licensing Agreements, Regulatory Obligations, IP Assets |
| **Security** | Visitor Roles, Access Credentials, Access Grants |
| **IT** | Devices, Software Licenses, User Accounts, Incidents |
| **Facilities** | Buildings, Floors, Rooms, Leases |
| **Governance** | Board Member, Committee Chair, Committee Member, Advisor Roles |

Plus `_shared/` for cross-cutting entities with no single owner.

## What Domain deliberately excludes

Domain does **not** include workflow states, approval steps, or
process logic. An `Order` doesn't have a field `is_approved_by_manager`
or `current_fulfillment_step`. Those are process concerns and live in
the Process layer. Keeping them out of Domain is what makes Domain stable.

## The "capability vs. process" distinction

- A **capability** is *what* the business can do: "We can fulfill orders."
  Noun-phrase. Lives in Domain.
- A **process** is *how* it's done: "Step 1: validate payment. Step 2:
  pick. Step 3: pack. Step 4: ship." Verb-phrase. Lives in Process layer.

## Primary Stewardship

Each Domain entity has exactly one **primary-steward capability**.
- `EmployeeRole` is HR's. Sales references it; doesn't redefine it.
- `Invoice` is Finance's. Procurement references it.
- Cross-cutting entities with no single owner live in `_shared/`.

## See also

- Domain principles: `docs/architecture/principles.md` (Domain section)
- Role-based pattern: `docs/patterns/role_based_relationships.md`
