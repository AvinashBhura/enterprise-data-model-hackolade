# Brownfield: an existing application database against the EDM

Use this when an application already has a database. The goal is to know how
far it is from the EDM, decide what to fix, and keep its model in this
repository from then on ([spec 0005](../../specs/0005-candidate-journey/spec.md),
requirements 13–14).

The idea in one line: **reverse-engineer, map, compare, report**.

## Steps

1. **Write the spec**, naming the database, its owner and the Domain
   subdomains it touches.
2. **Reverse-engineer** the database into a physical model in
   `src/04_application/<App>/<App>-<Target>.hck.json`:

   ```bash
   # from a live database (connection saved in Studio)
   hackolade revEng --target=PostgreSQL --connectName=<connection> \
     --model=src/04_application/<App>/<App>-PostgreSQL.hck.json
   # or from a DDL script
   hackolade revEngDDL --target=PostgreSQL --file=schema.sql --database=<db> \
     --model=src/04_application/<App>/<App>-PostgreSQL.hck.json
   ```

3. **Map it to the EDM.** For each table and column, bind the business glossary
   term (`hackolade/glossary/`) and set the `edmMapsTo` custom property to the
   Domain entity or attribute it holds, for example `TalentAcquisition.Candidate`
   or `TalentAcquisition.JobApplication.applied_date`. Leave it empty for purely
   technical columns.
4. **Derive the EDM-ideal model** for the same scope and target, as in the
   [greenfield workflow](greenfield.md), into a scratch file (not committed).
5. **Compare** the two models:

   ```bash
   hackolade compMod --model1=<ideal>.hck.json \
     --model2=src/04_application/<App>/<App>-PostgreSQL.hck.json \
     --deltaModel=/tmp/<App>-delta.hck.json
   ```

6. **Report the gaps:**

   ```bash
   python tools/report_gaps.py \
     --model src/04_application/<App>/<App>-PostgreSQL.hck.json \
     --domain src/02_domain/HR/TalentAcquisition/TalentAcquisition.hck.json \
     --delta /tmp/<App>-delta.hck.json --out gaps.md
   ```

   The report lists: tables and columns with no mapping; mapped columns whose
   type or allowed values differ from the Domain attribute; Domain attributes
   with no column.
7. **Decide and refactor.** For each gap: fix the database, fix the mapping, or
   accept it as a deviation with a reason. Record the decisions in the spec.
8. **Keep the model.** The reverse-engineered model, with its mappings, is the
   application's model in this repository. Repeat steps 4–6 when the Domain
   changes.

## Rules

- A brownfield model is never a parent of a Domain model.
- Mapping lives in the model (`edmMapsTo`, glossary terms), not in spreadsheets.
- Gaps are reported, not hidden: an accepted gap is a deviation with a reason.
