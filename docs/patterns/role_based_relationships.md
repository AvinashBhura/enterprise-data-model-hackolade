# Pattern — Role-Based Relationships

## The principle

> Relationships between parties are modeled as **Roles**, not as class
> hierarchies. A Person doesn't *become* an Employee — a Person *holds*
> an EmployeeRole.

## The problem this solves

Without roles, you'd represent each kind of engagement as a Person
subtype: `Employee extends Person`, `Vendor extends Person`,
`Visitor extends Person`. This breaks immediately because:

- A single human can hold multiple engagements at once (employee at
  one company AND vendor at a non-profit AND visitor to a partner site).
- Engagements end and resume; a Person who leaves and returns isn't a
  different Person.
- Subclass explosion: every combination of engagements would need its
  own multiple-inheritance subclass.

## The solution

```
Person (Foundation)              ← stable identity (one per human)
    └─ holds zero-or-more →
                                 Role (Foundation)         ← time-bound engagement
                                     └─ specialized as →
                                         EmployeeRole (HR)
                                         VendorRole (Procurement)
                                         VisitorRole (Security)
                                         CustomerContactRole (Sales)
                                         BoardMemberRole (Governance)
                                         ...
```

## Concrete shape

**Role** (Foundation):

| Attribute | Type | Note |
|---|---|---|
| `held_by_person` | relationship to Person | For Person-held roles |
| `held_by_organization` | relationship to Organization | For Organization-held roles |
| `role_type` | `enum` | |
| `effective_from` | datetime | Required |
| `effective_to` | datetime | |
| `lifecycle_state` | `enum` | The role's own lifecycle values |

**EmployeeRole** (Domain — HR) specialises Role (`foundationKind: Role`).
`held_by_person` is required (employees can only be people), and it adds:

| Attribute | Type |
|---|---|
| `employee_number` | string |
| `employing_organization` | relationship to Organization |
| `primary_position` | relationship to Position |

## Querying enterprise history

This pattern enables clean queries like:

> "Show me everything Priya Menon has ever done with our enterprise."

```
SELECT *
FROM Role
WHERE held_by_person = priya.entity_id
ORDER BY effective_from
```

One query. Returns every engagement — employee, vendor, visitor,
contractor, alumni — in time order. Without the Role pattern, you'd
need to query multiple tables and reconcile entities by some lossy
matching strategy.

## Operational rule: Role Immutability

A Role does not mutate its core terms once effective. Changes to
`employing_organization`, `primary_position`, or `employment_type` end
the current Role (set `effective_to`) and begin a new Role. The
existing record is preserved as history.

This is the right behavior for any "engagement" relationship — the
engagement *itself* changes. The original engagement is over; a new
one is starting.

## When `held_by` is ambiguous (Person OR Organization)

Some Roles can be held by either:
- `VendorRole` (an independent consultant Person, OR a vendor company Organization)
- `PartnerRole` (could be either)

For these, keep both typed references (`held_by_person`,
`held_by_organization`) with the rule that exactly one is filled. See
[polymorphic_references.md](polymorphic_references.md).

For Roles that are unambiguous (EmployeeRole is always held by a Person),
make `held_by_person` required.

## Anti-patterns to avoid

- **Specializing Person**: don't create `Employee extends Person`. Use `EmployeeRole`.
- **Embedding role data on Person**: don't put `employee_number` on Person. Put it on EmployeeRole.
- **Mutating role terms**: don't change `employing_organization` on a live EmployeeRole. End it; start a new one.
