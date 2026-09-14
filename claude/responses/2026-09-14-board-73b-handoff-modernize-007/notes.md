# notes.md — 2026-09-14-board-73b-handoff-modernize-007

Modernized, in the desk's order 5, 1, 4, 2, 6. Ten files, all inside
the forecast except one sentence in `bin/bale_report.py` (enumerated
under "Out-of-forecast drift" below). Every claim marked `observed`
was rehearsed in a staging-shaped copy of the shipped `context/` with
`files/` overlaid, `apply.sh` run, and the manifest at
`.bale-manifest.json`: `validation.sh` exited 0 with every observed
claim `[agree]`. The four handoff suites plus the happy suite run 31
tests in ~20 s with zero expected failures and zero unexpected
successes; the four checkpoint-adjacent suites run 64 tests (all
green with the slow gate open too — I ran them both ways).

This session went through one clarification round (thread round 1
→ 2, `bale relay`); the answers are applied below and named where
they changed a test body. `feedback.mechanical.linkage` records it.

## What changed, by path

**5 — forecast inheritance.** `cmd_handoff` reads the parent's
`scope.json` next to the goal, strictly: a new `read_recorded_scope`
in `bin/bale` returns `(scope, None)` or `(None, reason)`, and
`read_session_scope` now delegates to it and applies its whole-tree
degradation on top (its three log lines are byte-identical to
before). Resolution, first match wins: `--read-only` → `[]`;
`--write` → resolved set; parent record → as recorded, including
`[]`; no readable record → `resolved_scope(included_paths)`
undeclared. The reading plan is the read set only — it still ships in
`context/` and now goes to the blindness gate as `read_includes`. The
branch is journaled (`write forecast (inherited|write|read-only|fallback): …`)
and the summary's `inherited:` row names the forecast beside the goal.

**1 — disjointness gate.** The registry guard is gone. Pack's
`_run_scope_gate` closure is now `run_forecast_disjointness_gate` at
module level in `bale_pack.py`, with `caller` and
`declined_supersession` kwargs; the closure in `cmd_pack` is a
one-line delegate binding the declined-supersession note, and pack's
refusal text is byte-identical (`test_readonly_pack.py` pins its
marker; green). Handoff's variant says "handoff write forecast
intersects…", offers `--write` / apply / unlock, never
`--supersedes`, and its "without --write" note describes inheritance.
The passed line and the ADR-0006 several-open note are journaled
post-sid exactly as pack's are — inline, so `format_open_sessions_value`
was not needed and `bale_report.py` stayed untouched on this path.

**4 — `forecast_declared`.** The fallback branch passes `False`; the
other three pass `True`. A plan-less handoff with no readable parent
record now passes the blindness gate on the bare-pack rule (v0.4.9)
and records `["."]`, no admission stamp.

**2 — both halves.** `checkpoint_resolved_preflight` gains
`caller=` and swaps only the verb ("re-run this handoff"); handoff
passes `forecast=handoff_scope` so an inherited or declared `[]`
waives, stamped `checkpoint_waived: "read-only"` through the shared
builder. `--checkpoint-file` on handoff runs pack's sequence: the
front-loaded read and `{sid}`-base gate pre-tarball, the
`install_checkpoint_file` against the peeked sid immediately before
the resolved-existence pre-flight, the source-path + sha256 echo on
the summary and in the log. The `--read-only` contradiction refuses
pre-tarball with pack's wording.

**6 — the flags.** `--write` (pack's help text adapted; existence
rule and planner-bundle blindness mirrored, `--read-only`
contradiction), `--read-only`, `--checkpoint-file`. The other four
stay rejected; the `subTest` sweep pins them minus `--write` and
`--read-only`. The parser description no longer says "refuses while
any session is open".

**Riders.** `gather_files_for_pack(…, verbose=)` → `walk_for_pack`;
handoff passes `args.verbose`. The three ADR-0007 sentences are
deleted (`validation.sh` asserts their absence, plus the
"never empty by construction" sentence in the resolved-existence
docstring, which was the same claim). Five other `bale_pack.py`
docstring sentences describing handoff's old forecast shape were
corrected in place. `BALE.md`: the handoff command-table row rewritten
to the modern contract (one row, not a rewrite); the `scope.json`
tree comment, the §8.5 waiver paragraph ("`bale handoff` never
waives") and ledger row 30 each gained a re-basing clause, since each
asserted the old world. `bin/VERSION` → 0.4.28.

## Test-body rewrites (every one, per the round-2 answer)

Acceptance tests — decorators stripped:

- `test_handoff_admitted_beside_read_only_master`,
  `test_handoff_admitted_beside_scope_disjoint_worker`,
  `test_write_flag_is_accepted`, `test_refusal_named_remedy_is_accepted`
  — bodies as A wrote them, only the decorator and the docstring's
  "observed at 0.4.26" framing changed.
- `test_resumed_work_lands_on_the_parent_forecast` — one body change:
  the `recorded_scope(new) == recorded_scope(parent)` assertion moved
  ahead of the apply. As written it could never pass: a PASS merge
  wipes the session directory it reads. A never saw the test pass, so
  the ordering was never exercised.
- `test_planless_handoff_is_admitted_like_a_bare_pack` — the recorded
  scope assertion rewritten from `["."]` to `["hello.txt"]` (the
  parent's), per your ruling; a `BLINDNESS_PASSED_PHRASE` assertion
  added. The `["."]` outcome lives in
  `test_planless_fallback_without_parent_record` behind the knob.

Diagnosis pins that flipped by design — rewritten:

- `test_swap_is_visible_in_the_new_session_record` →
  `test_inheritance_is_visible_in_the_new_session_record`.
- `test_refusal_is_the_registry_guard_not_a_forecast_collision` →
  `test_refusal_is_a_forecast_collision` (a worker forecasting
  `hello.txt`; the refusal names the pair and `--write`; `--write
  other.txt` then admits it) plus `test_admission_is_journaled_like_packs`.
- `test_planless_stacks_both_gates` →
  `test_planless_handoff_inherits_and_meets_only_the_resolved_gate`.
- `test_planless_refusal_misdiagnoses_the_plan` →
  `test_covering_write_refuses_with_the_write_remedy` (pins the
  `bale_report.py` sentence: `--write claude` under a literal base
  refuses naming `--write`, never "re-bail").
- `test_pack_flags_are_rejected_at_argparse` →
  `test_remaining_pack_flags_are_rejected_at_argparse` (sweep minus
  `--write`, `--read-only`).

Passing tests re-pointed from the whole-tree fallback to the inherited
forecast (both had asserted the fallback with the parent's record
present, which inheritance makes unreachable):

- `HandoffManifestIsModernTest.test_whole_tree_handoff_stamps_modern_provenance_and_applies`
  → `test_planless_handoff_stamps_modern_provenance_and_applies`
  (base_files over `hello.txt` only; apply onto `hello.txt`).
- `test_handoff_happy.py::test_planless_handoff_resolves_whole_tree` →
  `test_planless_handoff_inherits_the_parent_forecast`. The happy
  suite's other two cases and its inline fixture are untouched.

New plain tests: read-only parent → child records `[]` (your ask);
`--write` overrides; `--write` grammar (missing path, contradiction);
`--read-only` overrides; fallback plan-less and fallback plan-citing
(forecast suite); fallback under `{sid}` and literal bases,
`--checkpoint-file` echo / idempotent re-run / contradiction,
read-only waiver (gates suite). Fixture: `drop_parent_record(sid)`.

## Out-of-forecast drift — admit at apply

- **`bin/bale_report.py`** — the `caller == "handoff"` branch of
  `format_checkpoint_scope_refusal` (one sentence) and the docstring
  paragraph describing it. Ratified in the thread (round 2, question
  2, as-recommended). Nothing else in the file changed; the queued
  apply-side session's territory is untouched.

`feedback.self_reported.forecast_departures` carries the same path.

## Judgment calls to ratify

- **An inherited forecast is *declared* to the blindness gate.** The
  record does not carry whether the parent typed `--write`; I chose
  the conservative direction. The alternative (`forecast_declared=False`
  for every inherited value) would let a parent admitted past the
  gate by `--allow-checkpoint-in-scope` hand off a child that renews
  the admission silently — exactly what v0.3.33's comment forbids.
  The residue: a parent whose include-set-default forecast happened
  to cover the oracle (a bare pack, or `--include claude/` with no
  `--write`) was admitted at pack as undeclared, and its plan-less
  handoff will refuse at the blindness gate. The refusal is loud and
  its remedies are real (`--write` narrower, or the admission flag);
  under the modern shape parents forecast with `--write`, so I expect
  this to be rare. If the ledger says otherwise, the fix is to record
  the declaration status beside the forecast, which is a scope-record
  change and a different session.
- **Two `bale_pack.py` refusal texts were mirrored into `bin/bale`**
  (the `--write` existence rule, the bundle-blindness refusal) rather
  than lifted to shared helpers: each is a few lines and pack's own
  copies sit inside `cmd_pack`'s flow with wizard-specific comments.
  A `CODE.md`-style extraction would touch pack more than this
  session should.
- `--checkpoint-file` on handoff has no wizard path (handoff has no
  wizard), so the `checkpoint_file_base_or_refuse` re-run pack does
  post-wizard is retained once, before the install, as pack's
  "one gate, both collection surfaces" comment describes.

## Surprises

- **The plan-less tests and the inheritance rule never met** in the
  fixture — every parent had a record, so `["."]` was unreachable.
  That was the clarification; the knob resolves it.
- **`unittest` exits 5 on "NO TESTS RAN"** (Python 3.12+), which the
  fixture-defines-no-tests assertion tripped over in rehearsal. The
  check keys on the `Ran 0 tests` line now. A's validation asserted
  the same thing; if it read the exit code, the desk's Python is
  older than the rehearsal box's.
- **The verbose rider's observed shape:** a *tracked* candidate the
  walk skips now prints its reason (`verbose: skip … (outside
  --include)` etc.), which is what A asked for. A cited path that is
  *untracked* never enters `git ls-files`, so it produces no line at
  all; it remains derivable only by subtracting `included` from
  `candidates`, as before. Naming the untracked drops explicitly
  would be a change to `walk_for_pack`, not to the rider — proposed
  below.
- **`exchange-record.schema.json` lags the manifest schema:** the
  v0.4.24 question-row `origin` key is admitted by
  `response-manifest.schema.json` but refused by `--emit-block`, so
  the round-1 manifest shipped without it. Desk-owned (`schemas/`),
  beside A's `base_files` echo note — which, I can confirm, is fixed:
  the provenance echo with `base_files` and `checkpoint` validated
  here.

## Proposals

- **What:** in `walk_for_pack --verbose`, print a `verbose: drop
  <path> (not tracked)` line for each include entry that matched no
  `git ls-files` path. **Why:** it is the one drop reason the rider
  cannot surface, and for a handoff it is the common one (a typo in a
  bailing worker's reading plan). **Scope hints:** `bin/bale_pack.py`,
  the walk; pack's `--verbose` suites.
- **What:** record the forecast's declaration status beside
  `scope.json` (or in the session's provenance record) so a handoff
  can inherit *declared-ness* as well as the value. **Why:** removes
  the residue named under judgment calls without weakening the
  no-silent-renewal rule. **Scope hints:** `persist_pack_session`, the
  registry readers, both request-building paths; after the ledger
  shows the case occurring.
- **What:** add `origin` to `exchange-record.schema.json`'s question
  row. **Why:** the two schemas should admit the same row, and the
  crafter refuses a manifest the lint accepts. **Scope hints:**
  `schemas/`, `bale_relay` / crafter parity tests; next schema
  session.
