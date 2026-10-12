#!/usr/bin/env bash
# Hackolade CLI steps used by CI (.github/workflows/hackolade.yml, release.yml)
# and by modellers locally (make hk-stale, hk-validate, hk-diff, hk-release).
#
#   ci/hk.sh stale    [model ...]   refresh a scratch copy of each model, fail if it changes
#   ci/hk.sh validate               forward-engineer every physical model with validation
#   ci/hk.sh diff     BASE [model ...]   compMod each model against git ref BASE, write a report
#   ci/hk.sh release  TAG           DDL, JSON Schema and docs for every model, plus a manifest
#
# HK is the command that runs the Hackolade CLI. Locally it is `hackolade`
# (Studio's CLI on your PATH). In CI it is the Docker image:
#   HK="docker compose -f ci/compose.yml run --rm hck" ci/hk.sh validate
# Models default to every .hck.json under src/. Output goes to build/ (never committed).
set -euo pipefail

HK=${HK:-hackolade}
PY=${PYTHON:-python3}
OUT=${OUT:-build}
cmd=${1:-}; shift || true

models() {
  if [ "$#" -gt 0 ]; then printf '%s\n' "$@"; else find src -name '*.hck.json' | sort; fi
}

kind() {  # polyglot or physical
  "$PY" -c 'import json,sys; m=json.load(open(sys.argv[1])); print("polyglot" if m.get("dbVendor")=="Polyglot" else "physical")' "$1"
}

has() {   # has FILE KEY -> true if the model has external references / derivation parents
  "$PY" -c 'import json,sys; m=json.load(open(sys.argv[1])); k=sys.argv[2]
v=m.get(k) or {}; v=v.get("properties", []) if isinstance(v, dict) else v
sys.exit(0 if v else 1)' "$1" "$2"
}

case "$cmd" in
  stale)
    # Refresh references and derivations on a copy of src/, then compare with the committed file.
    rm -rf "$OUT/stale" && mkdir -p "$OUT/stale" && cp -R src "$OUT/stale/src"
    failed=0
    for m in $(models "$@"); do
      copy="$OUT/stale/$m"
      has "$m" externalDefinitions && $HK extRefUpdate --model="$copy" --logLevel=2
      has "$m" polyglotModelPaths && $HK polyglotUpdate --model="$copy" --logLevel=2
      delta="$OUT/stale/$(basename "$m" .hck.json)-delta.hck.json"
      $HK compMod --model1="$m" --model2="$copy" --deltaModel="$delta" --logLevel=2
      if ! "$PY" ci/delta.py --empty "$delta"; then
        echo "STALE: $m is behind its parents. Refresh it in Studio (Tools > Polyglot > Update; refresh external references), review, save."
        failed=1
      fi
    done
    exit $failed
    ;;
  validate)
    mkdir -p "$OUT/ddl"
    for m in $(models "$@"); do
      [ "$(kind "$m")" = physical ] || continue
      name=$(basename "$m" .hck.json)
      $HK forwEng --model="$m" --path="$OUT/ddl/$name" --outputType=script --validateSchema=true --logLevel=2
      echo "validated $m -> $OUT/ddl/$name"
    done
    ;;
  diff)
    base=${1:?usage: ci/hk.sh diff BASE [model ...]}; shift
    mkdir -p "$OUT/diff"
    report="$OUT/diff/report.md"
    echo "## Model changes against \`$base\`" > "$report"
    for m in $(models "$@"); do
      name=$(basename "$m" .hck.json)
      if git cat-file -e "$base:$m" 2>/dev/null; then
        $HK compMod --model1="$base:$m" --model2="$m" --deltaModel="$OUT/diff/$name-delta.hck.json" --logLevel=2
        "$PY" ci/delta.py --summary "$OUT/diff/$name-delta.hck.json" --title "$m" >> "$report"
      else
        printf '\n### %s\n\nNew model.\n' "$m" >> "$report"
      fi
    done
    cat "$report"
    ;;
  release)
    tag=${1:?usage: ci/hk.sh release TAG}
    rel="$OUT/release/$tag"; rm -rf "$rel"; mkdir -p "$rel/ddl" "$rel/jsonschema" "$rel/docs"
    for m in $(models); do
      name=$(basename "$m" .hck.json)
      if [ "$(kind "$m")" = physical ]; then
        $HK forwEng --model="$m" --path="$rel/ddl/$name" --outputType=script --validateSchema=true --logLevel=2
      else
        $HK forwEng --model="$m" --path="$rel/jsonschema/$name" --outputType=jsonschema \
          --jsonSchemaCompliance=full --validateSchema=true --logLevel=2
      fi
      $HK genDoc --model="$m" --format=MARKDOWN --doc="$rel/docs/$name.md" --logLevel=2
    done
    $HK version > "$rel/hackolade-version.txt" 2>&1 || true
    "$PY" ci/manifest.py --tag "$tag" --version-file "$rel/hackolade-version.txt" --out "$rel/manifest.json"
    (cd "$OUT/release" && tar -czf "edm-$tag.tar.gz" "$tag")
    echo "release files in $OUT/release/edm-$tag.tar.gz"
    ;;
  *)
    sed -n '2,13p' "$0"; exit 2 ;;
esac
