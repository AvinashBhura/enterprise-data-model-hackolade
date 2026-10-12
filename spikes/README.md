# Spikes T1–T5 — Hackolade behaviour checks

Five behaviours the Hackolade documentation does not settle. Each takes 5–15
minutes in Hackolade Studio 8.13 or later (the 14-day trial includes the CLI).

No licence was available before the models were needed, so the specs were
completed first, using only patterns seen in Hackolade's own sample files
([D12](../docs/decisions/0012-complete-without-studio.md)). The spikes now run
as part of the [Studio verification runbook](../docs/workflows/studio-verification.md),
step 5: T1, T2 and T5 still decide follow-up work; T3 and T4 are answered by
opening and deriving the real models.

This folder is temporary. It is deleted when spec 0002 is Verified.

## Before you start

1. Studio 8.13 or later, with the PostgreSQL target plugin installed (Help > Plugin Manager). If the plugin's CLI target name is not `PostgreSQL`, use the name Plugin Manager shows in the commands below.
2. The three test models are already in `spikes/t4/generated/`: *EDM Spike Common*, *EDM Spike Foundation*, *EDM Spike Referrer*. They were written by `spikes/t4/generate.py` (re-run it to recreate them; the output is identical each time).
3. Work in a scratch copy: `cp -r spikes/t4/generated /tmp/spike && cd /tmp/spike`. Keep the generated files unchanged.

## How to report

Fill in `RESULTS.md` (template at the end) and copy the files Studio saved into
`spikes/results/`. The saved files matter most: they show how Studio stores
supertype groups and data types, which the converter must copy exactly.

---

## T4 — Converter-written files open, save and derive (do this first)

Decides D5: can a Python converter write model files, or must migration use Excel import?

1. Open each of the three files in Studio. Note any error or warning dialog, word for word.
2. In *EDM Spike Foundation*, check: four entities; `Role.held_by_person` shows a relationship line to Person; `Person.lifecycle_state` shows its six enum values; `Agreement.total_value` shows as a reference to AmountType.
3. Open the entity Properties pane for Person. Note whether the values `layer`, `foundationKind`, `entityType` appear anywhere (they will not show in the pane unless custom properties are configured; T5 covers that).
4. Save each file (Cmd/Ctrl+S) without changing anything. Copy the saved files to `spikes/results/t4-saved/`.
5. In *EDM Spike Referrer*: does `person` resolve to the Person entity? Does `expected_salary` resolve to AmountType? Use right-click > Refresh external references. Note each result.
6. If `expected_salary` does not resolve: delete it, then re-create it in Studio (right-click the entity > Reference > External definition > pick AmountType in *EDM Spike Common*). Save, and copy the file to `spikes/results/t4-reference-by-studio.hck.json`.
7. Derive *EDM Spike Foundation* to PostgreSQL (Tools > Polyglot > Derive, or the CLI below) and forward-engineer the DDL. Copy the DDL to `spikes/results/t4-foundation.sql`.

   ```bash
   hackolade polyglotDerive --target=PostgreSQL --polyglotmodels="EDM Spike Foundation.hck.json" --targetmodel=t4-pg.hck.json --pathType=relative
   hackolade forwEng --model=t4-pg.hck.json --path=./ddl --outputType=script
   ```

**Pass:** all three open with no error, both references resolve, and the DDL has tables `person`, `role`, `agreement` (and `entity`; T1 removes it) with a foreign key from `role` to `person`.

## T1 — A derived Foundation entity can be the supertype of a local entity

Decides D1 as approved: Foundation entities are derived into each domain model and specialised there.

1. Create a new Polyglot model *EDM Spike Domain*. Derive from *EDM Spike Foundation*, selecting only Role and Person.
2. Add an entity `Candidate` with two attributes: `candidate_number` (string) and `first_contact_date` (date).
3. Select the derived Role and choose Add subtype (Ctrl/Cmd+`)`). Make `Candidate` the subtype. Set the group: completeness partial, exclusivity disjoint, strategy **roll-down**.
4. Also add, to `Candidate`, one attribute of each of these types, so their stored form is captured: boolean, uuid (if offered), timestamp with time zone, integer.
5. Save. Copy the file to `spikes/results/t1-domain.hck.json`.
6. Derive *EDM Spike Domain* to PostgreSQL and forward-engineer DDL. Copy it to `spikes/results/t1-domain.sql`.
7. Back in *EDM Spike Foundation*: make `Entity` the supertype of Person, Role and Agreement (strategy roll-down), and mark `Entity` as **Polyglot only**. Save, copy to `spikes/results/t1-foundation.hck.json`. Derive to PostgreSQL again and copy the DDL to `spikes/results/t1-foundation.sql`.
8. In the PostgreSQL model derived in step 6, try to change the group strategy for this one target (to preserved hierarchy). Note whether Studio allows it.

**Pass:** step 3 is allowed on a derived entity; the step 6 DDL has a `candidate` table carrying Role's columns and no `role` table; the step 7 DDL has `entity_id` on each table and no `entity` table.

**Record also:** whether step 8 is allowed (spec 0005 relies on application models being able to choose their own strategy).

## T2 — An externally referenced entity can be a supertype

If this passes, D1 switches to references (no derived copies of Foundation entities in domain models).

1. Create a new Polyglot model *EDM Spike Domain 2*. Add an entity `Role`, then in its Properties pane set `$ref` to an external reference: *EDM Spike Foundation*, entity Role.
2. Try Add subtype on it, with a new entity `Candidate`.
3. If allowed, save, copy to `spikes/results/t2-domain.hck.json`, derive to PostgreSQL, copy the DDL to `spikes/results/t2-domain.sql`.

**Pass:** step 2 is allowed and the DDL matches T1 step 6.

## T3 — A shared value type derives to plain columns

Decides the D2 exception (Amount and Quantity stay shared definitions).

1. Look at the DDL from T4 step 7 for `agreement.total_value`.

**Pass:** two plain columns (for example `total_value_value numeric` and `total_value_currency varchar`), not one JSON column.

**If it fails:** repeat the derive with "Normalize complex data types in separate entities" turned on and off (CLI: `--normalize=true`). Note what each gives.

## T5 — Custom properties from the repository work in the CLI Docker image

Decides whether the metadata checks can also run inside Hackolade in CI.

1. Build the official image from [hackolade/docker](https://github.com/hackolade/docker/tree/main/Studio) with a valid licence.
2. Copy a custom-properties configuration for the Polyglot target into the image's Hackolade options folder (one entity-level text property `foundationKind` is enough).
3. Run `forwEng --outputType=jsonschema --jsonSchemaCompliance=full` on *EDM Spike Foundation* inside the container.

**Pass:** `foundationKind` appears in the JSON Schema output for each entity.

**If you have no concurrent licence:** mark T5 as "not run". The Python checks cover metadata without it.

---

## RESULTS.md template

```markdown
# Spike results

Studio version:            (Help > About)
Edition:                   Trial / Professional / Workgroup
PostgreSQL plugin version:
Date:

| Spike | Result | Notes |
| --- | --- | --- |
| T4 | Pass / Fail | errors on open; did both references resolve? |
| T1 | Pass / Fail | step 8 allowed? |
| T2 | Pass / Fail | |
| T3 | Pass / Fail | column names produced |
| T5 | Pass / Fail / Not run | |

Anything surprising:
```
