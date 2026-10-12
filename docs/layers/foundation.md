# Layman's Guide — Foundation Layer

## What it is in one sentence

The permanent, universal concepts that define what an enterprise
fundamentally consists of — people, organizations, teams, activities,
roles, agreements, assets, addresses.

## Why it matters

Every enterprise — hospital, bank, retailer, software company — deals
with people, organizations, activities, and agreements. The specifics
differ wildly; the underlying concepts don't. Foundation captures
these concepts once, properly, so every system and integration uses
the same definition of "a Person" or "an Organization".

## A real-world example

When HR says "employee," Finance says "payroll recipient," and IT says
"user account holder," they're all talking about the same human being.
Without a Foundation layer, each department builds its own version of
a Person — and when those versions disagree, you get the classic
enterprise nightmare: the same person appearing three times in three
systems with slightly different names, addresses, birthdays.

Foundation says: **there is one Person. Everything else is a view of
that Person.**

## The Nine Concrete Entities

| Entity | Plain Language |
|---|---|
| **Entity** | The semantic anchor — every concept declares "I am an enterprise thing" by inheriting from Entity. |
| **Person** | A human being. Stable identity for all engagements. |
| **Organization** | Abstract formal body. Subtypes: LegalEntity, OrganizationalUnit. |
| **Team** | Purposeful group of people. Independent — not an Organization subtype. |
| **Role** | Time-bound engagement. The pivot for "who plays what with whom." |
| **Activity** | Something happening in time. |
| **Agreement** | Formal commitment between parties. |
| **Asset** | Thing of value, owned or managed. |
| **Address** | Location reference. |

## Why it rarely changes

The concept of "a person" has meant the same thing for centuries.
"An organization" has meant the same thing since commerce began.
If your Foundation layer is changing often, something is wrong —
you've probably let something volatile sneak in where it doesn't
belong.

## What lives nested inside Foundation

The **Common sub-layer** (`01_foundation/common/`) holds the shared
toolkit Foundation entities are built from: value types and the
generic taxonomy model. See [`common.md`](common.md).

## See also

- Foundation principles: `docs/architecture/principles.md` (principles 1–7)
