#!/usr/bin/env bash
# Blind checkpoint — board 49a-ii (the `bale open` verb)
# Re-derived at the 2026-08-24-continue-plan-005 desk from the 49a v1
# oracle (sha256 56d5784e…), per the checkpoint-tracks-scope rule,
# from the request, before implementation. v1 of this session's
# lineage.
#
# Derivation record (desk-side; probes named for the HOLD card):
#   P1 kept verbatim from 49a v1.
#   P2 derived: probe token renamed to carry the reserved
#      .bale-bundle suffix — the recognizer landed with 49a-i, so
#      the missing-file path is probed under the real suffix.
#   P3 retired: the pairs-pin rider was struck from the registry and
#      consumed at the sub-master contract-doc landing; the pin
#      passes at base and no longer belongs to this scope.
#   P4 re-derived: v1's BALE.md grep stopped discriminating once
#      §6.7 landed ("bale open" appears at base). New invariant:
#      the verb self-describes at the help surface.
#   P5 new: BALE.md no longer claims the verb does not exist —
#      §6.7's "Neither exists yet" sentence is stale the moment the
#      verb lands, and truing it up is part of the outcome.
#   P6 new: boards 36/40's landed hash fields are verified by the
#      verb — a bundle whose manifest hash mismatches its member
#      bytes refuses as bale's own refusal, not a crash. The fixture
#      manifest was dry-run envelope-valid against the shipped
#      validate_bundle_manifest at the desk, so the probed refusal
#      is the hash one.
#
# Outcome-only by design, unchanged from v1's posture: subcommand
# wiring, flag surface, echo text, the dry-run leg's rendering, the
# expected-HOLD proof format, argv-replay mechanics, delivery-flag
# injection, and the row-48 decision are deliberately unprobed —
# they are spec in the brief or the worker's latitude, and pinning
# them would bind mechanism.
#
# Contract: runs in staging (cwd = staging root) beside
# validation.sh; [PASS]/[FAIL]/[SKIP <reason>] per probe; exit 0
# all-pass, 1 any-fail, 2 script error. All matching is
# whitespace-normalized (wrap-tolerant, standing desk rule); sid
# patterns are date-agnostic (none used here). Dry-run at the desk
# against the applied base (0.4.12): all 5 probes FAIL.
set -u
FAILS=0
p() { printf '%s\n' "$1"; }
fail() { p "[FAIL] $1"; FAILS=$((FAILS+1)); }
pass() { p "[PASS] $1"; }

if ! command -v python3 >/dev/null 2>&1; then
  p "[SKIP] all probes: python3 not found"
  exit 0
fi

norm() { tr -s '[:space:]' ' ' < "$1"; }

# P1 — the open verb exists: `bale help open` resolves and exits 0.
if out=$(python3 bin/bale help open 2>&1); then
  pass "P1 bale-open-verb-exists (bale help open exit 0)"
else
  fail "P1 bale-open-verb-exists: bale help open exited nonzero: $(printf '%s' "$out" | head -c 200)"
fi

# P2 — a missing bundle refuses loudly as bale's own refusal (not an
# argparse unknown-command error), and the refusal names what was not
# found. Token chosen to appear nowhere else; suffix is the reserved
# recognizer.
tok="nonexistent-bundle-49a-probe.bale-bundle"
out=$(python3 bin/bale open "/tmp/$tok" 2>&1)
rc=$?
if [ "$rc" -ne 0 ] \
   && ! printf '%s' "$out" | grep -qi "invalid choice" \
   && printf '%s' "$out" | grep -q "$tok"; then
  pass "P2 missing-bundle-refuses-loudly (rc=$rc, names the path)"
else
  fail "P2 missing-bundle-refuses-loudly: rc=$rc, output: $(printf '%s' "$out" | head -c 200)"
fi

# P4 — the verb self-describes: its help output says what it
# consumes. One topical word pinned; all wording is the worker's.
out=$(python3 bin/bale help open 2>&1)
if printf '%s' "$out" | grep -qi "bundle"; then
  pass "P4 bale-open-help-mentions-bundle"
else
  fail "P4 bale-open-help-mentions-bundle: help output never says 'bundle': $(printf '%s' "$out" | head -c 200)"
fi

# P5 — BALE.md no longer claims the verb does not exist. §6.7's
# pre-landing sentence ("Neither exists yet", covering this verb and
# 49b) is false once the verb lands; the true-up is part of the
# outcome. Wrap-tolerant; how the sentence is rephrased is the
# worker's.
if [ -f "BALE.md" ] && ! tr -s '[:space:]' ' ' < BALE.md | grep -q "Neither exists yet"; then
  pass "P5 bale-md-staleness-trued-up (no 'Neither exists yet')"
else
  fail "P5 bale-md-staleness-trued-up: BALE.md still claims the verb does not exist"
fi

# P6 — hash verification is real (boards 36/40): a bundle whose
# manifest sha256 mismatches its member bytes refuses — nonzero,
# bale's own refusal, not a traceback. Fixture built fresh in an
# isolated temp dir (per-scenario isolation); manifest shape
# dry-run envelope-valid at the desk; argv is harmless (--read-only)
# by defensive construction.
fixdir=$(mktemp -d) || { p "[SKIP] P6: mktemp failed"; fixdir=""; }
if [ -n "$fixdir" ]; then
  printf '%s\n' "#!/usr/bin/env bash" "exit 0" > "$fixdir/checkpoint.sh"
  cat > "$fixdir/bundle.json" <<'JSON'
{
  "bundle_format": 1,
  "pack_argv": ["probe-goal", "--slug", "probe-49aii-fixture", "--read-only", "--no-edit"],
  "members": {
    "brief": null,
    "checkpoint": {"path": "checkpoint.sh", "sha256": "0000000000000000000000000000000000000000000000000000000000000000"}
  },
  "pre_answered": []
}
JSON
  bundle="$fixdir/2026-08-24-probe-49aii-fixture.bale-bundle"
  tar -czf "$bundle" -C "$fixdir" bundle.json checkpoint.sh
  out=$(python3 bin/bale open "$bundle" 2>&1)
  rc=$?
  if [ "$rc" -ne 0 ] \
     && ! printf '%s' "$out" | grep -qi "invalid choice" \
     && ! printf '%s' "$out" | grep -q "Traceback (most recent call last)"; then
    pass "P6 tampered-bundle-refuses (rc=$rc, refusal not crash)"
  else
    fail "P6 tampered-bundle-refuses: rc=$rc, output: $(printf '%s' "$out" | head -c 200)"
  fi
  rm -rf "$fixdir"
fi

if [ "$FAILS" -gt 0 ]; then
  p "checkpoint: $FAILS probe(s) failed"
  exit 1
fi
p "checkpoint: all probes passed"
exit 0
