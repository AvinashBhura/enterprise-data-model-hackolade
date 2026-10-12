# ci — Hackolade CLI for CI and local runs

**Owner:** EDM architecture. Spec: [0006](../specs/0006-ci-cd-and-ai-assets/spec.md).

| File | Does |
| --- | --- |
| `Dockerfile` | Hackolade's CLI image (`hackolade/hck-cli`, pinned tag, Studio 8.13+) plus this repository's custom properties and naming files |
| `compose.yml` | Runs that image on this repository: repository at `/data/repo`, read-only root filesystem, `/data` and `/tmp` writable |
| `plugins.txt` | Plugins the repository needs, with minimum versions; checked by `check_plugins.py` against the image's `version` output |
| `hk.sh` | The Hackolade steps: `stale`, `validate`, `diff`, `release`. Used by the workflows and by `make hk-*` |
| `delta.py` | Reads a `compMod` delta model: empty or not, and a Markdown summary |
| `manifest.py` | Writes the release manifest: tag, commit, Studio and plugin versions, model checksums |
| `spec_gate.py` | Fails a pull request that changes `src/`, `tools/`, `config/` or `hackolade/` without naming an Approved spec |

## Workflows (`.github/workflows/`)

| Workflow | When | Needs a licence |
| --- | --- | --- |
| `governance.yml` | every pull request and push to `main` | no: `make test`, `make check`, spec gate |
| `hackolade.yml` | pull requests that change `src/` | yes: stale gate, schema gate, DDL smoke test on PostgreSQL 16, change report as a PR comment. Without the `HACKOLADE_LICENSE` secret it reports "skipped: no licence" and passes |
| `release.yml` | tags `v*` | yes: DDL, JSON Schema, Markdown docs and manifest, attached to the GitHub release |

Third-party actions are pinned to full commit hashes; Dependabot proposes updates.

## Licence

The CLI in Docker needs a **concurrent (floating)** licence; a workstation licence does not work in containers. Store the key as the repository secret `HACKOLADE_LICENSE`. It is passed to `validateKey` at run time and never written to a file.

## Running locally

With Studio installed and its `hackolade` command on your PATH:

```bash
make hk-stale        # are my models behind their parents?
make hk-validate     # forward-engineer physical models with validation
make hk-diff         # what changed against main
```

Or through Docker, with a floating licence: `HK="docker compose -f ci/compose.yml run --rm hck" make hk-validate`.

**To verify on first use** (docs/workflows/studio-verification.md): that `hackolade/hck-cli:8.13.0` exists (otherwise pin the first 8.13+ tag); that the CLI reads the custom properties from the copied options folder (spike T5); and how an empty `compMod` delta looks (`delta.py --empty`).
