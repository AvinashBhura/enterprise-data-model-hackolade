# Pattern — Bitemporal Modeling

## The principle

The `Temporal` base type provides **bitemporal validity** — both
*valid-time* (when a fact is true in the real world) and
*transaction-time* (when the fact was recorded in the system).
Apply Temporal selectively, not universally.

## The two times

| Time | What it captures | Example |
|---|---|---|
| **Valid-time** (`valid_from`, `valid_to`) | When the fact is/was true in the real world | "Priya's salary was $X from 2024-01-01 to 2024-12-31" |
| **Transaction-time** (`recorded_from`, `recorded_to`) | When the system knew about the fact | "We recorded Priya's salary on 2024-01-15; we corrected the start date on 2024-02-03" |

## When to apply Temporal

Apply `Temporal` when both questions matter:
- When was this true?
- When did we know it was true?

**Good fits**: Roles, Agreements, CompensationPackages, classifications,
state transitions where backdating or future-dating may occur.

**Skip Temporal** when only present-state matters:
- Address (use Lifecycleable instead — superseding addresses captured
  via state_history)
- Reference data like Position (rarely backdated)

Per the **Minimalism** Foundation principle: don't apply base types
where they don't earn their place.

## The Temporal base type

An entity lists `Temporal` in `edmComposes` and declares these attributes,
as the contract in `config/edm-rules.yaml` says ([D2](../decisions/0002-base-type-attributes-on-entities.md)):

| Attribute | Type | Meaning |
|---|---|---|
| `valid_from` | datetime | Start of the real-world validity period |
| `valid_to` | datetime | End of the real-world validity period (open if empty) |
| `recorded_from` | datetime | When this record began to exist in the system |
| `recorded_to` | datetime | When this record ceased to exist in the system (if superseded) |

## Temporal queries

**As of a real-world date** ("what was Priya's salary on 2024-06-15?"):
```
SELECT * FROM CompensationPackage
WHERE held_by_role = priya.employee_role.entity_id
  AND valid_from <= '2024-06-15'
  AND (valid_to IS NULL OR valid_to > '2024-06-15')
  AND recorded_to IS NULL  -- still believed correct
```

**As of a system-knowledge date** ("what did we believe about Priya's
salary on 2024-02-01?"):
```
SELECT * FROM CompensationPackage
WHERE held_by_role = priya.employee_role.entity_id
  AND recorded_from <= '2024-02-01'
  AND (recorded_to IS NULL OR recorded_to > '2024-02-01')
```

**Both at once** ("what did we believe on 2024-02-01 about her salary
on 2024-06-15?"):
```
WHERE valid_from <= '2024-06-15'
  AND (valid_to IS NULL OR valid_to > '2024-06-15')
  AND recorded_from <= '2024-02-01'
  AND (recorded_to IS NULL OR recorded_to > '2024-02-01')
```

## Corrections vs amendments

- **Correction**: we knew the wrong fact. Update `recorded_to` on the
  bad record; insert a new record with the correct fact (same
  `valid_from`, new `recorded_from`).
- **Amendment**: a new fact takes effect. Update `valid_to` on the
  superseded record; insert a new record with new `valid_from`.

These two are distinct: corrections rewrite our knowledge of the past;
amendments record genuine real-world changes.

## When NOT to bitemporal-model

If you only ever care about "what's true now," and corrections are
handled by overwrite, plain `Lifecycleable` is sufficient. Bitemporal
adds query complexity and storage cost; only apply when audit or
historical reconstruction requires it.

In practice, Roles, Agreements, and high-stakes Activities are good
candidates. Most other entities don't need it.
