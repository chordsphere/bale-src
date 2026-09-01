#!/usr/bin/env bash
# board-70 blind checkpoint v3 — shipped-doc reachability.
# (v3 derives from v2: ONLY P5 changes — v2's P5 pinned the deny
# pattern's literal spelling, a mechanism assertion that HOLDs any
# equally valid implementation, e.g. a whitespace-class regex over
# the guard's raw-text scan. P1-P4 are byte-identical to v2. v3's
# P5 asserts the outcome: the guard rejects a planted wrapped
# instance and stays green on the clean tree, implementation-free.)
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

# P5 — the self-containment guard denies the pointer class, as an
# outcome: run the guard suite twice on a hermetic copy of the
# tree — the clean copy must be green; a copy with a planted,
# wrapped "own"-variant instance in a scanned doc must go red. The
# guard self-roots from its own file path, so the copy grades
# itself, whatever the deny's implementation.
tmpd=$(mktemp -d) || { echo "[CHECKPOINT-ERROR] mktemp failed"; exit 2; }
cp -r docs tools tests schemas "$tmpd"/ 2>/dev/null \
  || { echo "[CHECKPOINT-ERROR] tree copy failed"; rm -rf "$tmpd"; exit 2; }
( cd "$tmpd" && python3 -m unittest discover -s tests \
    -p 'test_global_doc_selfcontainment.py' ) >/dev/null 2>&1
clean_rc=$?
printf "stray note: see the bale tool's own\ndocumentation for details.\n" \
  >> "$tmpd/docs/CODE.md"
( cd "$tmpd" && python3 -m unittest discover -s tests \
    -p 'test_global_doc_selfcontainment.py' ) >/dev/null 2>&1
planted_rc=$?
rm -rf "$tmpd"
probe "P5-guard-denies-pointer-class (clean=$clean_rc planted=$planted_rc; want 0/nonzero)" \
      "$([ "$clean_rc" -eq 0 ] && [ "$planted_rc" -ne 0 ]; echo $?)"

if [ "$fail_count" -gt 0 ]; then
  echo "checkpoint: HOLD ($fail_count probe(s) failed)"
  exit 1
fi
echo "checkpoint: PASS (5/5)"
exit 0
