# Greenfield: a new application model from the EDM

Use this when an application's database is designed from scratch. Example:
[Candidate Journey](../../src/04_application/CandidateJourney/README.md)
([spec 0005](../../specs/0005-candidate-journey/spec.md)).

The idea in one line: **derive, then design**. The application model starts as a
copy of the logical entities it needs, keeps a live link to them, and adds only
physical choices on top.

## Steps

1. **Write the spec.** List the entities the application owns, the entities it
   only uses (owned by another system), the target database and the physical
   design rules. Get it approved ([specs/README.md](../../specs/README.md)).
2. **Pick the parent models.** Usually one Domain subdomain model, the core
   process model and `04_application/_shared/ApplicationShared`. Add
   `01_foundation/Foundation` only for a Foundation entity the application
   stores itself (Candidate Journey stores `person`).
3. **Derive.** In Studio: *Tools > Polyglot > Derive*. Or with the CLI:

   ```bash
   hackolade polyglotDerive --target=PostgreSQL \
     --polyglotmodels="src/02_domain/HR/TalentAcquisition/TalentAcquisition.hck.json;src/03_process/_core/CoreProcess.hck.json" \
     --targetmodel=src/04_application/<App>/<App>-PostgreSQL.hck.json --pathType=relative
   ```

   Select only the entities the application owns. Keep *normalize* off unless
   the spec says arrays must become child tables.
4. **Apply the physical design**, each change as a deviation in the derived
   model, never in the parent:
   - schema (container) and technical names (snake_case, from the naming convention);
   - primary key `entity_id` as `uuid`; unique constraints for natural keys;
   - foreign keys only between tables of this model; references to entities
     owned elsewhere stay `uuid` columns, with their source keys in
     `source_system_reference`;
   - indexes on foreign keys and on the columns the application filters by.

   Give every changed table a `deviationReason` (`make check-deviations`). Never
   change an entity derived from the Foundation, except for a physical data
   type (`deviations.physical_type_keys`).
5. **Document the physical design** in the application folder's README, as a
   list someone could re-apply after a fresh derivation.
6. **Check and generate.**

   ```bash
   make check
   make hk-validate        # forwEng --validateSchema=true on every physical model
   ```

   CI runs the generated DDL against an empty PostgreSQL 16 database.
7. **Keep it current.** When a parent changes, run `polyglotUpdate` (Studio:
   *Tools > Polyglot > Update*), review the impact screen and save. CI's stale
   gate fails a pull request whose application model is behind its parents.

## Rules

- The derivation link is never broken: no "detach", no copy-paste of entities.
- The application model never becomes a parent of a Domain model.
- The application repository commits the DDL it deploys; this repository does
  not (D4).
