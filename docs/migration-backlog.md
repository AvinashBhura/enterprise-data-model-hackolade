# Migration backlog

Content not carried over when the EDM moved from LinkML to Hackolade ([D6](decisions/0006-migration-scope.md)). Everything here is recoverable from tag `linkml-final-v0.5.0` of the earlier repository, [AvinashBhura/enterprise-data-model](https://github.com/AvinashBhura/enterprise-data-model) ([D13](decisions/0013-separate-hackolade-repository.md)). Run these in a clone of that repository:

```bash
git show linkml-final-v0.5.0:<path>          # one file
git archive linkml-final-v0.5.0 <folder> | tar -x   # a whole folder
```

Each item is migrated, if needed, under its own spec. Nothing here is converted automatically.

## Migrated

Rebuilt in Hackolade by the specs below, from the LinkML source at the tag, by
`migration/build.py`. Awaiting Studio verification
([D12](decisions/0012-complete-without-studio.md)). `python migration/compare.py`
lists every difference from the tag, each with its reason.

| Content | Path at the tag | Now | Spec |
| --- | --- | --- | --- |
| Foundation and Common | `src/01_foundation/` | `Foundation`, `CommonValueTypes`, `CommonTaxonomy` | [0002](../specs/0002-foundation-and-common/spec.md) |
| The six taxonomy schemas | `src/01_foundation/common/taxonomies/` | data for `CommonTaxonomy`: [taxonomies-to-load.md](taxonomies-to-load.md) | [0002](../specs/0002-foundation-and-common/spec.md) |
| HR domain | `src/02_domain/HR/` | five subdomain models, plus Talent Acquisition | [0003](../specs/0003-hr-and-talent-acquisition/spec.md) |
| Core process model | `src/03_process/_core/` | `CoreProcess` | [0004](../specs/0004-core-process-model/spec.md) |
| Application shared constructs | `src/04_application/_shared/` | `ApplicationShared` | [0005](../specs/0005-candidate-journey/spec.md) |

## Frozen domains

Migrate one domain per spec, after HR (spec 0003) is Verified. Use the matching domain taxonomy workbook as the target structure.

| Domain | Path at the tag | Schemas | Entities |
| --- | --- | --- | --- |
| Facilities | `src/02_domain/Facilities/` | 6 | Building, Floor, Lease, Room |
| Finance | `src/02_domain/Finance/` | 12 | Account, Budget, CostCenter, FiscalPeriod, Invoice, JournalEntry, Payment |
| Governance | `src/02_domain/Governance/` | 5 | AdvisorRole, BoardMemberRole, CommitteeChairRole, CommitteeMemberRole |
| IT | `src/02_domain/IT/` | 8 | Device, Incident, SoftwareLicense, UserAccount |
| Legal | `src/02_domain/Legal/` | 8 | IntellectualPropertyAsset, LicensingAgreement, NDA, RegulatoryObligation |
| Procurement | `src/02_domain/Procurement/` | 8 | PurchaseOrder, PurchaseRequisition, VendorContract, VendorRole |
| Sales | `src/02_domain/Sales/` | 10 | Account, CustomerContactRole, Opportunity, Order, OrderLine, Quote |
| Security | `src/02_domain/Security/` | 6 | AccessCredential, AccessGrant, VisitorRole |
| Domain `_shared` | `src/02_domain/_shared/` | 1 | LegalEntityReference (no single owner; governed by the EDM steering committee) |

## Retired sample processes

Examples built on the LinkML core process model. The core model itself is migrated by spec 0004. Process definitions are data, created by applications, so these are not expected to return as schemas.

| Process | Path at the tag | Schemas |
| --- | --- | --- |
| ContractLifecycle | `src/03_process/ContractLifecycle/` | 3 |
| IncidentResolution | `src/03_process/IncidentResolution/` | 3 |
| InvoiceApproval | `src/03_process/InvoiceApproval/` | 3 |
| Offboarding | `src/03_process/Offboarding/` | 3 |
| Onboarding | `src/03_process/Onboarding/` | 3 |
| OrderFulfillment | `src/03_process/OrderFulfillment/` | 3 |
| PurchaseApproval | `src/03_process/PurchaseApproval/` | 3 |

## Retired sample application models

LinkML projection examples. Real application models are built with the greenfield or brownfield workflow (spec 0005).

| Application | Path at the tag | Schemas |
| --- | --- | --- |
| Okta | `src/04_application/Okta/` | 4 |
| SAP | `src/04_application/SAP/` | 5 |
| Salesforce | `src/04_application/Salesforce/` | 5 |
| ServiceNow | `src/04_application/ServiceNow/` | 4 |
| Workday | `src/04_application/Workday/` | 5 |

## Foundation and Common content handled by spec 0002

| Content | Path at the tag | Where it goes |
| --- | --- | --- |
| Base types (mixins) | `src/01_foundation/common/base/` | Attributes declared on each entity; contracts in `config/edm-rules.yaml` ([D2](decisions/0002-base-type-attributes-on-entities.md)). Value types move to `CommonValueTypes.hck.json` |
| Lifecycle and type enums (16) | `src/01_foundation/common/codelists/lifecycles/`, `.../types/` | `enum` lists on the owning attributes ([D3](decisions/0003-enumerations-on-attributes.md)) |
| ISO code lists (5) | `src/01_foundation/common/codelists/standards/` | Format rules on attributes; no values stored ([D3](decisions/0003-enumerations-on-attributes.md)) |
| Taxonomies (6) | `src/01_foundation/common/taxonomies/` | Data in the Common taxonomy model ([D11](decisions/0011-common-taxonomy-model.md)); example hierarchies go to `docs/taxonomies-to-load.md` |

## Other retired content

| Content | Path at the tag | Why |
| --- | --- | --- |
| Capability pages | `docs/capabilities/` | One page per frozen domain. Returns with each domain's migration |
| Instance examples | `examples/` | LinkML instance data. The EDM is a schema store, and the brief asks for no extra examples |
| Generators | `generators/` | Hackolade generates all artifacts ([D4](decisions/0004-generation-by-hackolade.md)) |
| LinkML validation tools and tests | `tools/`, `tests/` | Replaced by checks that read Hackolade model files (spec 0001) |
| LinkML config | `linkml-config.yaml` | Not needed |
