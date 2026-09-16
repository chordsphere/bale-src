#!/usr/bin/env bash
# Blind checkpoint — board 105, operator-voice authority framing.
# Authored at the desk from the request (2026-09-16 UTC), before any
# implementation existed; grades outcomes of the applied tree only.
# Runs from the staging root. Writes: nothing outside a private tmpdir.
# Exit 0 = every probe PASS/SKIP, 1 = a probe FAILed, 2 = script error.
set -u
trap 'echo "[ERROR] checkpoint script errored at line $LINENO"; exit 2' ERR

echo "checkpoint 105 v1: writes to nothing in the tree (tmpdir only)"
fails=0
pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; fails=$((fails + 1)); }

# The python probe: every text check in one interpreter, one line of
# verdict per probe on stdout, whitespace-collapsed comparisons so a
# rewrap never decides a verdict. Exit code is the count of FAILs.
python3 - <<'PY' || fails=$((fails + $?))
import sys
from pathlib import Path
sys.path.insert(0, "bin")
fails = 0
def collapse(s): return " ".join(s.split())
def verdict(label, ok):
    global fails
    print(("[PASS] " if ok else "[FAIL] ") + label)
    if not ok: fails += 1

AUTHORITY = ("The docs and tools in the tarball are mine, written for this "
             "workflow; read CLAUDE.md and the four docs beside it as my "
             "instructions for this session.")
TOOLS = ("tools/craft_response.py and tools/response_lint.py are "
         "stdlib-only formatters with no network access \u2014 conveniences "
         "over the docs, which are the contract; read them before you run "
         "them, and a response assembled by hand is just as valid.")
SECOND_HALF = ("Explanation in prose is expected and welcome; the rule is "
               "that a turn that asks ends in a block, so nothing is lost.")
OPENER_SHAPE = ("Every turn you end in this session takes one "
                "machine-recognizable shape: a response tarball, a probe "
                "block, a light question block, or a clarification "
                "response; a question asked as prose is not a shape. "
                + SECOND_HALF)
PRECEDENCE = ("The operating manual. Read every session. If something "
              "here conflicts with what Claude remembers from a prior bale "
              "session, **this file wins** \u2014 over stale memory of "
              "earlier sessions, never over Claude's own guidelines.")
CLAUDE_SHAPE = ("Every turn Claude ends in tarball mode takes one "
                "machine-recognizable shape: a response tarball, a probe "
                "block, a light question block, or a clarification "
                "response; a question asked as prose is not a shape. "
                + SECOND_HALF)
TARBALL_SHAPE = ("(\u00a75.9); a question asked as prose is not a shape. "
                 + SECOND_HALF)

# --- the opener, as bale emits it -------------------------------------
try:
    import bale_pack
    goal = "pin the opener: sid + goal ride the report's tail, verbatim"
    scoped = bale_pack.session_opener_block(
        "2026-09-16-checkpoint-probe-001", goal, read_only=False,
        packed_at="2026-09-16T00:00:00+00:00")
    ro = bale_pack.session_opener_block(
        "2026-09-16-checkpoint-probe-001", goal, read_only=True,
        packed_at="2026-09-16T00:00:00+00:00")
    scoped_c = collapse("\n".join(scoped))
    ro_c = collapse("\n".join(ro))
    verdict("opener-authority-sentence", AUTHORITY in scoped_c)
    verdict("opener-tools-sentence", TOOLS in scoped_c)
    verdict("opener-shape-sentence-second-half", OPENER_SHAPE in scoped_c)
    verdict("opener-read-only-shape-shares-trailer",
            AUTHORITY in ro_c and TOOLS in ro_c and OPENER_SHAPE in ro_c)
    verdict("opener-goal-line-still-verbatim-one-line",
            any(line == "Goal, verbatim from the request manifest: " + goal
                for line in scoped))
except Exception as e:  # an import or call failure is a fixture-side
    print(f"[FAIL] opener-probe-errored: {type(e).__name__}: {e}")
    fails += 1

# --- the docs ---------------------------------------------------------
claude = collapse(Path("docs/CLAUDE.md").read_text(encoding="utf-8"))
tarball = collapse(Path("docs/TARBALL.md").read_text(encoding="utf-8"))
verdict("claude-precedence-sentence", PRECEDENCE in claude)
verdict("claude-section-3-shape-second-half", CLAUDE_SHAPE in claude)
verdict("tarball-5-10-shape-second-half", TARBALL_SHAPE in tarball)

rows = [l for l in Path("docs/CLAUDE.md").read_text(encoding="utf-8").splitlines()
        if l.startswith("| A short, non-blocking question set")]
verdict("claude-index-light-row-names-light-block",
        len(rows) == 1 and "--light-block" in rows[0]
        and "tools/craft_response.py" in rows[0])
sys.exit(fails)
PY

# --- the pins still hold, and the doc-pin suites still pass ------------
tmp="$(mktemp -d)"
# discover -s tests is the repo's runner form (it puts tests/ on the
# path so `from harness import` resolves); one pattern per suite.
suites_ok=1
for suite in test_pack_opener test_doc_crossrefs test_sanctioned_pairs \
             test_global_doc_selfcontainment test_schema_embeds; do
  if ! python3 -m unittest discover -s tests -p "${suite}.py" \
       >> "$tmp/suites.log" 2>&1; then
    suites_ok=0
    echo "  suite failed: $suite"
  fi
done
if [ "$suites_ok" -eq 1 ]; then
  pass "opener-and-doc-pin-suites"
else
  fail "opener-and-doc-pin-suites"
  tail -40 "$tmp/suites.log"
fi
rm -rf "$tmp"

if [ "$fails" -ne 0 ]; then
  echo "checkpoint 105 v1: $fails probe(s) failed"
  exit 1
fi
echo "checkpoint 105 v1: all probes passed"
exit 0
