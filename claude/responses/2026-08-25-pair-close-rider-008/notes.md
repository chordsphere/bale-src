# notes.md — 2026-08-25-pair-close-rider-008

All five cargo items landed; every `changes[]` path sits inside the
stamped forecast (BALE.md, bin/VERSION, docs/CLAUDE.md, tests as a
directory entry — which covers the new tests/test_slow_gate.py and
the fifteen decorated suites — and validate.sh), so there is no
out-of-forecast enumeration to admit. The tree shipped at 0.4.15
exactly, so the bump proceeded; no clarification, no probe.

## The --slow survey: criterion, inventory, and the wall

I timed all 582 cases individually (unittest run per case, wall
clock). No single case dominates — the cost is a long tail of
sandbox-building E2E cases at 0.7–2.5s each — so the gate is a
per-case selection, by a criterion you can audit rather than a list
you have to trust:

**Gated: cases measured >= 0.7s, except each test class keeps its
fastest such case ungated as a default-run representative.** The
exception is what keeps every behavior cluster smoke-covered on the
default run — without it, ApplyRealOperationsTest (deletes, renames,
exec bits) and a few others would have vanished from the default
suite entirely. Result: **40 cases gated across 15 suites; 10
representatives deliberately kept default.**

The ten kept representatives, so you can see what stayed:
test_forecast_ledger epoch/departures full path;
test_apply_preflight row-8 dirty-on-target;
test_auto_sweep rollback-then-undo and unset-byte-identity;
test_apply_operations forgotten-chmod-caught;
test_hold_retry_e2e validation-exit2-holds;
and four test_archive_dir cases (one per class).

Worth a beat of review: the gated set includes both
BareApplyResolutionTest cases — board 51's own feature, gated the
session after it landed. They met the criterion (0.78s each, class
has lighter siblings covering the pre-flight surface), and they run
on every BALE_TEST_SLOW=1 pass; if you'd rather the newest feature
ride the default run for a few boards, un-decorating those two costs
~1.6s of default wall.

**Measured walls (build machine, two runs — the second ran ~16%
slower globally, so read the pair as variance bounds, and the ratio
as the durable fact):**

| run | before | after (default) | after (full, BALE_TEST_SLOW=1) |
|-----|--------|-----------------|--------------------------------|
| 1 | 138.9s | 99.0s | 136.3s |
| 2 | — | 119s | 158s |

The default run is ~72% of the full wall. Against the ~2 min full
suite your board-50 note measured, that projects a default wall
around 85–100s on your machine — under the 120s target with real
headroom for the next generation-heavy suite, which is the fold-in's
stated point. The threshold cases (~0.68–0.72s) jitter run to run;
the decorators fix the selection, so jitter only means the split may
be slightly off-optimal on your hardware, never irreproducible. The
manifest defers a local re-time as the cheap follow-up if the
default wall surprises you.

## Shapes and placements to ratify

- **The helper.** `SLOW_ENV_VAR = "BALE_TEST_SLOW"` (constraint
  spelling, pinned by test), a `slow_gate()` factory, and the
  module-level `slow` decorator in tests/harness.py. Only the
  literal value `"1"` opens the gate — `yes`, `true`, `" 1"` stay
  closed, and the skip reason names the exact spelling, so a
  half-set gate fails loud in the skip line. The factory exists so
  test_slow_gate.py can exercise both states without re-imports.
- **validate.sh surface.** A check plus a hint, not a test runner:
  when a tests/ tree is present (bale-src checkout) it asserts
  harness.py carries the gate and prints the gate's current state;
  on a release install (no tests/) it `[SKIP]`s with a note. The two
  state lines use a new `  [INFO]` marker — they are not checks and
  must not move the pass/fail counters; existing markers were only
  PASS/FAIL/SKIP. Flag if you'd rather they be bare printfs. I also
  kept the new section's comment free of BALE.md citations, since
  validate.sh ships in the release, which has no BALE.md.
- **BALE.md placements.** The bare-apply paragraph opens section 8,
  directly after the "workhorse" paragraph — the one spot that
  documents apply's invocation forms. The verbatim-required sentence
  sits on its own never-wrapped line (byte-exact including
  backticks; grep -Fx'd in validation.sh per the
  derive-don't-rewrite corollary — a line-based probe can only pin
  an unwrapped line). The gate's docs line rides section 13's v0.4
  selftest paragraph, the harness's own section. The 7.7 opener tag
  follows the section's sibling convention ("(v0.3.31, board-6
  ...)", "(v0.4.10, revG)"): "(v0.4.16, board 52 — ...".
- **docs/CLAUDE.md.** The pointer is one parenthetical sentence
  appended inside the "When the chat preamble and the manifest goal
  disagree" subsection, right after the drift-cause sentence it
  qualifies; "bale-emitted" verbatim. The doc-crossref and
  self-containment suites run inside the default suite pass and are
  green over the edit.

## Validation notes

- `validation.sh` runs the gated suite by default and gates its own
  full-suite pass behind `--slow` (TARBALL.md 7.6) — the board-50
  response's local `--slow` spelling, now pointed at the one home.
  Default validation wall lands near the target on this machine;
  budget ~2 min, ~4.5 min with `--slow`.
- The **"repo validate.sh end-to-end" claim is `predicted`, not
  observed**: my staging was built from the shipped `context/`,
  which (correctly) omits README.md, upgrade.sh, and scripts/, so
  validate.sh's presence rows for those failed *here*. Every failing
  row named one of those absent files; all rows my change touches —
  the slow-gate section, `--version reports 0.4.16` — passed. In
  real bale staging (full repo + overlay) it should exit 0. If it
  doesn't, the reconciliation block will print the [DISAGREE] and
  the failing rows.
- apply.sh is one `chmod +x validate.sh` (the mirror strips the
  bit); validation.sh carries the paired 7.7 assertion, both emitted
  from the crafter's `--executable` list.
