# src — the model files

Every EDM model is a Hackolade model file (`.hck.json`) under one of the layer folders below. A model belongs to the layer of the folder it sits in, and may depend only on models in its own or a lower layer (`make check-layers`).

| Folder | Layer | Holds |
| --- | --- | --- |
| `01_foundation/common/` | Common (rank 0) | Shared value types; the generic taxonomy model |
| `01_foundation/` | Foundation (rank 1) | The 11 Foundation concepts |
| `02_domain/` | Domain (rank 2) | One polyglot model per subdomain, in `<Domain>/<Subdomain>/` |
| `03_process/` | Process (rank 3) | The core process model |
| `04_application/` | Application (rank 4) | Physical models, one folder per application |

Model files are created and changed in Hackolade Studio or with the Hackolade CLI only. Never hand-edit them. Every change starts with an approved [spec](../specs/README.md).
