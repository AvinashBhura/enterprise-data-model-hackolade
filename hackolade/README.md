# hackolade — Hackolade Studio settings in Git

Hackolade reads these per user from `~/.hackolade/options`. Install or update them with `make hackolade-config` (dry run) and `make hackolade-config FORCE=1` (apply, after a backup), then restart Studio.

| Folder | Holds |
| --- | --- |
| `customProperties/Polyglot/` | EDM custom properties on an **EDM** tab: model (`edmLayer`, `edmDomain`, `edmSubdomain`, `edmBuiltBy`), entity (`layer`, `foundationKind`, `entityType`, `steward`, `edmComposes`, `edmConnects`, `edmValueType`, `edmAbstract`, `semanticUri`, `sourceTaxonomyRef`, `deviationReason`), attribute (`dataClassification`, `edmMapsTo`, `semanticUri`, `valueDefinitions`) |
| `customProperties/PostgreSQL/` | The same tab for PostgreSQL physical models: model (`edmLayer`), table (`steward`, `edmMapsTo`, `deviationReason`), column (`dataClassification`, `edmMapsTo`, `semanticUri`, `valueDefinitions`) |
| `naming/` | `abbreviations.csv`, the conversion file for business-to-technical names. Empty for now: the EDM uses full words |
| `glossary/` | `edm-glossary.csv`, the EDM glossary in Hackolade's glossary format (Term_ID, Term, Description, Domain). Assign it to a model in Studio with Actions > Assign Glossary |

**To verify on first use.** The custom-property files follow Hackolade's published template. They put EDM properties on their own tab so they do not depend on the names of Studio's built-in tabs. Spike T5 confirms they load; report any property that does not appear.

**Naming settings** are not stored here yet: Hackolade does not document their file. `make hackolade-config` prints the values to set by hand.
