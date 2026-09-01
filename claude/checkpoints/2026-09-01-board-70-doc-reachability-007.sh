#!/usr/bin/env bash
# board-70 blind checkpoint v2 — shipped-doc reachability.
# (v2 derives from v1: header wording only; every probe byte-identical.)
# Outcome contracts only. Runs at the applied tree's root.
# Exit 0 = all probes pass; exit 1 = HOLD (labels above name the
# failures); exit 2 = the checkpoint itself could not run.
set -u

fail_count=0

norm() {  # whitespace-normalized bytes of a file, wrap-tolerant
  tr -s ' \t\n' '   ' < "$1"
}

need() {  # a file the checkpoint itself depends on
  if [ ! -f "$1" ]; then
    echo "[CHECKPOINT-ERROR] missing file: $1"
    exit 2
  fi
}

probe() {  # probe LABEL EXPR-RESULT(0 pass / nonzero fail)
  local label="$1" rc="$2"
  if [ "$rc" -eq 0 ]; then
    echo "[PASS] $label"
  else
    echo "[FAIL] $label"
    fail_count=$((fail_count + 1))
  fi
}

for f in docs/CLAUDE.md docs/TARBALL.md docs/DOCS.md docs/CODE.md \
         docs/PLANNER.md tools/craft_response.py \
         tests/test_global_doc_selfcontainment.py; do
  need "$f"
done

# P1 — the unnamed-pointer class is gone from every request-carried
# surface (five docs + both request-carried tools), wrap-tolerant.
hits=0
for f in docs/CLAUDE.md docs/TARBALL.md docs/DOCS.md docs/CODE.md \
         docs/PLANNER.md tools/craft_response.py \
         tools/response_lint.py; do
  [ -f "$f" ] || continue
  c=$(norm "$f" | grep -oiE "(bale )?tool's (own )?documentation" | wc -l)
  hits=$((hits + c))
done
probe "P1-pointer-class-gone (expected 0, found $hits)" \
      "$([ "$hits" -eq 0 ]; echo $?)"

# P2 — PLANNER.md points the planner role at the shipping
# surfaces: the request-carried crafter and the installed schema.
norm docs/PLANNER.md | grep -q "tools/craft_response.py" \
  && norm docs/PLANNER.md | grep -q "schemas/bundle-manifest.schema.json"
probe "P2-planner-repoints-to-shipping-surfaces" "$?"

# P3 — TARBALL.md's bundle passage names the schema's installed
# path as the format's mechanical home.
norm docs/TARBALL.md | grep -q "schemas/bundle-manifest.schema.json"
probe "P3-tarball-names-schema-home" "$?"

# P4 — CLAUDE.md carries the reachability model, naming both
# request-carried tools.
norm docs/CLAUDE.md | grep -q "craft_response.py" \
  && norm docs/CLAUDE.md | grep -q "response_lint.py"
probe "P4-claude-reachability-paragraph" "$?"

# P5 — the self-containment guard denies the pointer class (the
# pattern text is present in the guard file, wrap-tolerant).
norm tests/test_global_doc_selfcontainment.py \
  | grep -qi "tool's documentation\|tool's (own )?documentation"
probe "P5-guard-denies-pointer-class" "$?"

if [ "$fail_count" -gt 0 ]; then
  echo "checkpoint: HOLD ($fail_count probe(s) failed)"
  exit 1
fi
echo "checkpoint: PASS (5/5)"
exit 0
