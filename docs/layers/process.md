# Layman's Guide — Process Layer

## What it is in one sentence

The workflows, steps, transitions, and events that describe how
a capability is actually executed — versioned and immutably bound,
referencing (but never modifying) Domain entities.

## Why it matters

Business processes change constantly. Your order fulfillment process
this year is different from last year because you added a warehouse,
or a regulation changed, or you shaved two steps. If every process
change required changing `Order`, the Domain layer would churn endlessly.

The Process layer absorbs that volatility. It says: **processes are
their own citizens, versioned and tracked, but they don't get to
modify the stable nouns of the business.**

## A real-world example

A large company has five concurrent onboarding processes:
- US Engineering → process v3.2
- EMEA Sales → process v2.1
- Contractors → process v1.4
- Executives → process v1.0
- Interns → process v2.0

All five operate on the same Domain entities (`EmployeeRole`,
`Position`, `OnboardingChecklist`). None modifies them — they
*orchestrate* activities using them. When US Engineering updates to
v4.0, the others are unaffected. Domain is unaffected.

This is the payoff: many processes, one stable Domain, clean separation.

## The Seven Process Families

Plus `_core/` containing the abstractions every family extends.

| Family | Purpose |
|---|---|
| `_core/` | Generic abstractions: ProcessDefinition, ProcessInstance, ProcessStep, StepCompletion, ProcessTransition, ProcessEvent |
| `Onboarding/` | Hiring new EmployeeRoles and ContractorRoles |
| `Offboarding/` | Separating EmployeeRoles; creating AlumniRoles |
| `OrderFulfillment/` | Customer order pick → pack → ship → invoice |
| `InvoiceApproval/` | AP invoice approval workflows |
| `PurchaseApproval/` | Requisition / PO approval workflows |
| `IncidentResolution/` | IT incident detection → resolution → postmortem |
| `ContractLifecycle/` | Drafting → negotiation → renewal → termination |

## Why processes are versioned

When Priya starts onboarding on March 28 under v3.2, and v4.0 launches
on April 1, Priya's onboarding continues under v3.2. Process
definitions are *snapshots in time*; instances bind to a snapshot for
their entire lifetime. This is the **Frozen-Contract** principle.

## The four Process principles

1. **Borrower** — Process uses Domain; never edits it.
2. **Snapshot** — Every definition is versioned.
3. **Ledger** — State lives in events, pointing to domain entities.
4. **Frozen-Contract** — An instance's binding never changes.

## See also

- Process principles: `docs/architecture/principles.md` (Process section)
- Process versioning pattern: `docs/patterns/process_versioning.md`
- Worked example: `examples/priya_onboarding/`
