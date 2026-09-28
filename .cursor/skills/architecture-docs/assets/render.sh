#!/usr/bin/env bash
# Render docs/diagrams/*.d2 to SVG. `--check` fails if any committed SVG is stale.
# D2 output depends on its version, so renders are pinned to one.
set -euo pipefail
cd "$(dirname "$0")"
want=v0.9.0
have=$(d2 --version)
[[ $have == "$want" ]] || { echo "need d2 $want, have $have" >&2; exit 1; }

stale=0
for src in [!_]*.d2; do
  svg=${src%.d2}.svg
  if [[ ${1:-} == --check ]]; then
    tmp=$(mktemp --suffix=.svg)
    d2 --theme 0 "$src" "$tmp" >/dev/null 2>&1
    cmp -s "$tmp" "$svg" || { echo "stale: docs/diagrams/$svg" >&2; stale=1; }
    rm -f "$tmp"
  else
    d2 --theme 0 "$src" "$svg" >/dev/null
  fi
done
exit $stale
