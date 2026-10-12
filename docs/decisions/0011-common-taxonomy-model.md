# D11 — One generic, versioned taxonomy model in Common

Status: Accepted
Date: 2026-10-12
Approved by: Avinash Bhura, in the [transition strategy document](https://claude.ai/code/artifact/5f38deb5-5ee0-414e-9516-58e23c95726c)

## Context

The LinkML Common layer had six separate taxonomy schemas, each with a simple node list.

## Decision

One generic schema in `CommonTaxonomy.hck.json` stores every enterprise taxonomy as data, combining four techniques: adjacency list (the source of truth), closure table, materialised path, and SCD Type 2 bounded by named versions. Tables: `taxonomy`, `taxonomy_version`, `taxonomy_node`, `taxonomy_closure`, `transaction_hierarchy`. Only `parent_node_key` is edited; closure rows and paths are derived in the same transaction. Published versions never change. `transaction_hierarchy` is append-only.

## Consequences

Accepted trade-offs: moves and renames near the top rewrite whole subtrees; one parent per node; no foreign key from `transaction_hierarchy` to the classified record (allowed entity names are checked); business dates are per version, not per row. The six old taxonomy schemas become data.
