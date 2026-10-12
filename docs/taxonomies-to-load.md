# Taxonomies to load

The EDM stores schemas, not data (D3). The six taxonomy schemas of the old
Common layer are replaced by one generic model,
[`CommonTaxonomy`](../src/01_foundation/common/README.md) (D11). Each old
taxonomy becomes **data** in that model: one `taxonomy` row, one first
`taxonomy_version` (DRAFT, then PUBLISHED), and its nodes as `taxonomy_node`
rows with their `taxonomy_closure` rows.

This page hands the example hierarchies over to the reference-data owners. They
are starting points, not approved content. Each owner confirms or replaces the
hierarchy before it is loaded by the application that maintains taxonomies.

| taxonomy_code | Name | source_standard | Owner (proposed) | Used to classify |
| --- | --- | --- | --- | --- |
| `POSITION_TYPE` | Position Type | SOC, where it fits | HR (Workforce Planning) | Position |
| `ORGANIZATION_TYPE` | Organization Type | — | EDM architecture | Organization (with `organization_type`) |
| `GEOGRAPHY` | Geography | ISO 3166-1 at country level | Finance (reporting) | Address, LegalEntity, reporting roll-ups |
| `INDUSTRY` | Industry Classification | GICS, NAICS, ISIC or SIC (one taxonomy per scheme) | Sales / Procurement | external Organizations, LegalEntity |
| `CHART_OF_ACCOUNTS` | Chart of Accounts | — | Finance | Finance accounts (one taxonomy per legal entity if needed) |
| `ASSET_TYPE` | Asset Type | — | IT / Facilities | Asset |

How a classification is recorded: a `transaction_hierarchy` row names the
record (`transaction_entity`, `transaction_id`), the node and node version, and
both paths as they stood. Allowed entity names are in `config/edm-rules.yaml`
(`polymorphic_references`, entity `TransactionHierarchy`).

## POSITION_TYPE

Job families. Align with SOC where it fits.

```text
Technical
├── Engineering
│   ├── Software Engineering
│   │   ├── Backend
│   │   ├── Frontend
│   │   └── Full-Stack
│   └── Hardware Engineering
├── Data & Analytics
└── Design
Business
├── Sales
├── Marketing
├── Finance
└── Legal
Operations
Customer-Facing
```

## ORGANIZATION_TYPE

Kinds of organisation unit and which kind may contain which. This is not an
organisation chart: an actual "Engineering Division" is an Organization record.

```text
LegalEntity
├── BusinessUnit
│   └── Division
│       └── Department
│           └── Group
│               └── Team
│                   └── Squad
├── Subsidiary        (alternate under LegalEntity)
└── JointVenture      (alternate under LegalEntity)
RegulatoryBody        (separate root, outside the internal hierarchy)
Partner               (separate root, outside the internal hierarchy)
```

The flat list of the same values is the `organization_type` enum on
Organization.

## GEOGRAPHY

Regional roll-ups for reporting. The country level uses ISO 3166-1 alpha-2
codes as `node_code`.

```text
World
└── Region (AMER, EMEA, APAC, LATAM)
    └── Country
        └── State/Province
            └── City
```

## INDUSTRY

One taxonomy per scheme (`INDUSTRY_GICS`, `INDUSTRY_NAICS`...), since a node
has one parent. Typical GICS structure:

```text
Sector (e.g., Information Technology)
└── Industry Group (e.g., Software & Services)
    └── Industry (e.g., Software)
        └── Sub-Industry (e.g., Application Software)
```

## CHART_OF_ACCOUNTS

The abstract structure for financial reporting. Account records live in the
Finance domain. An enterprise may keep one global chart or one per legal entity.

```text
Assets
├── Current Assets
│   ├── Cash & Equivalents
│   ├── Accounts Receivable
│   └── Inventory
└── Non-Current Assets
    ├── Property, Plant & Equipment
    └── Intangible Assets
Liabilities
├── Current Liabilities
└── Long-Term Liabilities
Equity
Revenue
Expenses
```

## ASSET_TYPE

```text
Physical
├── Equipment
│   ├── IT Equipment
│   │   ├── Laptop
│   │   ├── Desktop
│   │   ├── Server
│   │   └── Network Device
│   └── Office Equipment
├── Vehicle
└── Real Estate
    ├── Building
    └── Land
Digital
├── Software License
├── Domain Name
└── Dataset
Financial
├── Cash
├── Receivable
└── Investment
Intellectual Property
├── Patent
├── Trademark
└── Copyright
```
