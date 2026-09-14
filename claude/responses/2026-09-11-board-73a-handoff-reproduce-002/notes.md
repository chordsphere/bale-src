# notes.md — 2026-09-11-board-73a-handoff-reproduce-002

Reproduce-only, as briefed. Four new files under `tests/`, all inside
the forecast; nothing under `bin/` or the docs was touched. Seventeen
new tests: six `@expectedFailure` reproductions, eleven plain passing
tests (pack-side controls, non-reproductions, and diagnosis pins that
assert the exact refusal an operator sees today). Discovery is green:
`Ran 20 tests ... OK (expected failures=6)` including the happy test's
three, ~13s.

The short version: the operator's report is consistent with **five**
distinct failures on the handoff path, and the two the brief did not
predict are the ones that best fit its wording. Every one of them is a
gate or a value that handoff shares with pack but calls the way pack
called it at v0.3.x — pack has been re-based twice since (ADR-0015 at
v0.4.1, the v0.4.9 default-pack change) and handoff never was.

## Per-path diagnosis

Line regions named by stable phrase; verify against the bytes.

### 1. Beside an open session — lead 1, reproduced

*Gate:* the registry guard in `cmd_handoff` ("Handoff opens a new
session; refuse while any session is open"). It runs before the
bailout tarball is opened, fails on any non-empty `open_sessions(repo)`,
and never reads `read_session_scope`. Pack, on the identical forecast
(`hello.txt`), passes the ADR-0015 forecast-disjointness gate beside
the same open session — both beside a read-only master (empty
forecast) and beside a worker forecasting `other.txt`. Pinned:
`test_handoff_registry_gate.py`, two expectedFailures with two
pack-side controls.

*Kind:* design-era mismatch, and the code says so in its own comment
("Admitting a handoff beside a scope-disjoint open session — pack's
ADR-0007 gate — is deliberately not extended here"). The comment
predates ADR-0015 as well as ADR-0007's re-basing; under it the modern
orchestration shape (read-only master always open) makes handoff
mechanically unreachable, which the brief's hypothesis called
correctly.

*Why it read as something else:* the refusal names the open sid and
`bale apply` / `bale unlock`, and says nothing about forecasts. An
operator who followed it would `unlock` the master — closing the desk
session — and then handoff would proceed. That is the plausible chain
behind "no adherence to forecast disjointness": the operator knew the
gate existed for pack and saw handoff ignore it. The diagnosis pin
asserts the refusal's silence on forecasts, and that nothing is
consumed (peeked sid unchanged, no session state).

*Modernizing touches:* replace the guard with a call into pack's
`_run_scope_gate` (currently a closure inside `cmd_pack`; it would need
lifting to module level in `bale_pack.py` with `declined_supersession`
parameterized) against `handoff_scope`, sited after the reading-plan
resolution — which means the guard moves from pre-tarball to
post-extraction. The `.gitignore` guard and the tarball extraction
would then run before the gate; both are side-effect-free apart from
the auto-commit, which pack also does pre-gate. The ADR-0006 "several
open" disambiguation note pack prints would need mirroring, and
`format_open_sessions_value` in `bale_report` already handles the
list.

### 2. `{sid}`-templated checkpoint — lead 3, reproduced with a twist

*Gate:* `checkpoint_resolved_preflight(repo, peek_session_id(repo,
slug))` — the same call pack makes. With a plan citing `hello.txt`,
the blindness gate passes (forecast does not cover the pattern) and
the resolved-existence gate refuses: HEAD has no
`claude/checkpoints/<peeked-sid>.sh`. Pinned:
`test_handoff_checkpoint_gates.py::HandoffSidBaseTest`.

*The twist, which I think is a defect rather than a mismatch:* the
refusal is emitted verbatim on both callers, and its **first-listed
remedy is `--checkpoint-file <file>`** ("bale commits it ... and packs
in the same run"). Handoff's argparse rejects the flag — exit 2,
`unrecognized arguments`. The operator who follows the refusal's own
instructions gets a second failure with no visible relation to the
first. The refusal also says "re-run this pack". The v0.4.10 remedy
wording ("Refusals name their real remedy and their real actor") is
the standard this fails against. The `expectedFailure` asserts the
named remedy is accepted; the passing companion asserts the second
remedy (hand-commit at the peeked path, re-run) converges on the same
sid and stamps the resolved checkpoint — that half works exactly as
designed.

*Kind:* the gate itself is a design-era mismatch (v0.4.8 added the
gate to both callers; v0.4.10 added the flag to pack only). The remedy
text is a defect — it promises a path the surface lacks.

*Modernizing touches:* `p_handoff` gains `--checkpoint-file`;
`cmd_handoff` gains the `locate_and_read_checkpoint_file` +
commit-at-resolved-path sequence pack runs between the peek and the
allocation (pack's helper is already a function in `bale_pack.py`;
the call site is ~15 lines). Alternatively `checkpoint_resolved_preflight`
gains a `caller` kwarg like the blindness gate has, so the refusal
names only remedies the caller offers — the cheaper change, and the
one that fixes the defect without deciding the mismatch.

### 3. Literal checkpoint, plan cites a file — lead 3's other half, NOT reproduced

Handoff proceeds, stamps `provenance.checkpoint` with the HEAD hash,
`checkpoint_scope_admitted: false`, and the resulting session's normal
response applies with "checkpoint provenance stamp verified" and the
checkpoint run in staging. Pinned as a passing test. The literal-base
gate (`git cat-file -e HEAD:<path>` inside the blindness pre-flight)
is a no-op when the oracle is committed, and there is no per-session
resolution to miss. So on a project *not* shaped like bale-src, lead 3
does not fire; the operator's project shape matters for the
diagnosis, and it is unknown.

### 4. Plan-less handoff versus a bare pack — NOT predicted by any lead

This is the first of the two lines the brief asked me to say plainly.

*Gate:* `checkpoint_blindness_preflight(repo, handoff_scope, ...)`
with `handoff_scope == ["."]` (the plan-less fallback
`resolved_scope([])`) and `forecast_declared` at its `True` default.
`scope_covers_path(["."], <any checkpoint>)` is true, so the forecast
half refuses. A bare `bale pack` — no `--include`, no `--write` — in
the same project resolves the same `["."]` but passes
`forecast_declared=False` (v0.4.9: "make the bare default pack
possible in a checkpoint-configured project") and auto-excludes the
oracle from context. Observed: literal base, plan-less handoff exit 1
at the blindness refusal; bare pack in the same repo exit 0 with the
auto-exclusion line and `scope.json == ["."]`. Pinned:
`HandoffLiteralBaseTest`, expectedFailure plus the bare-pack control.

Under a `{sid}` base the two gates stack: blindness refuses; with
`--allow-checkpoint-in-scope` (the one flag handoff carries) the
resolved-existence gate refuses next, and the operator is back at
path 2. Pack clears both in one run with `--checkpoint-file`
(observed, not pinned — it is pack's behavior and pack's suites own
it). Pinned as a passing diagnosis test that shows the stacking.

*Kind:* design-era mismatch with a stale comment. `cmd_handoff` says
"such a handoff refuses without the flag, the same way a default
whole-tree pack does" — true at v0.3.33, false since v0.4.9. And the
refusal text is wrong for this caller: its first remedy is "re-bail
with a reading plan that does not cite the checkpoint", but the plan
cited nothing; the coverage came from the fallback. (The blindness
gate's `caller` kwarg swaps only the narrowing-remedy sentence, and
that sentence assumes coverage came from a citation.) The happy test
pins the `["."]` fallback "AS-IS" with a standing watch on exactly
this friction; this is the watch materializing, plus the v0.4.9
asymmetry the watch predates.

*Modernizing touches:* pass `forecast_declared=bool(extracted_paths)`
(or, equivalently, `included_paths != []`) from `cmd_handoff` — the
plan-less fallback is the include-set-compatibility shape and should
take the include-set rule; one argument at one call site. The
`caller="handoff"` remedy sentence in `format_checkpoint_scope_refusal`
needs a plan-less variant. Note that a `{sid}` base under a plan-less
handoff would still need path 2's remedy.

### 5. The forecast swap — NOT predicted, and the best fit to the report

The second plain line.

*Code path:* `handoff_scope = resolved_scope(included_paths)` — the
reading-plan file set — recorded to `scope.json`, stamped as
`resolved_scope`, and used for `base_files`. `cmd_handoff` never opens
`.bale/sessions/<responds_to>/scope.json`; it reads only the parent's
`manifest.json`, and only for `goal`. The comment is explicit: "On the
handoff path the read set and the forecast coincide by construction."

That sentence is ADR-0007's definition of scope ("a session's scope is
its resolved include set"), which ADR-0015 overturned at v0.4.1
("includes gate nothing"). Handoff was written under 0007 and is the
one request-building path the 0015 flip did not reach.

*Observed:* parent packed `--include hello.txt --include other.txt
--write other.txt` (records `["other.txt"]`); bailout's reading plan
cites `hello.txt` (what to *read* next — the natural thing for a
bailing worker to write, per TARBALL.md §5.7's section name); handoff
exit 0, records `["hello.txt"]`, output mentions neither `other.txt`
nor any forecast (its `inherited:` line names the goal only); a normal
response modifying `other.txt` — the path the parent forecast — is
refused at apply with the own-forecast drift REJECT naming `other.txt`
against `write forecast: hello.txt`. Pinned:
`test_handoff_forecast.py`, expectedFailure (apply lands; the new
record equals the parent's) plus a passing pin of every artifact the
swap writes.

This is, I think, the literal reading of row 73: "apply trouble"
(apply-side REJECT), "no adherence to forecast" (the response landed
where the *original* forecast said and the handoff session's forecast
disagreed), on a session whose argv the operator could not have
narrowed ("apparently old syntax" — there is no `--write`). It also
requires no open sibling session and no checkpoint configuration —
the two preconditions the leads assumed — so it is reachable on any
project that has ever packed with `--write`.

*Kind:* design-era mismatch in mechanism, defect in effect. Nothing
handoff promises is broken by its own terms; but ADR-0015 clause 4
says the forecast is the ask, `notes.md` and the ledger grade
departures from *it*, and a handoff continuing the same goal under a
silently different ask corrupts that measurement — the resumed
session's drift rate is measured against a forecast nobody declared.

*Modernizing touches:* read `read_session_scope(repo, responds_to_sid)`
next to the goal inheritance; use it as `handoff_scope` when present
and non-empty; keep the reading-plan set as the *read* set only
(`context_entries` — that part is already right); pass
`read_includes=included_paths` to the blindness gate now that read
and forecast differ (the gate already supports it); fall back to the
reading-plan set — or `["."]`, per path 4 — only when the parent's
record is missing or the parent was read-only (a read-only parent
cannot have bailed on landed work, but the case needs a decision).
`--write` on handoff (path 6) is the override for when the bailing
worker's `handoff.md` argues the ask changed.

### 6. The argv surface — lead 2, confirmed as a mismatch

`--write`, `--include`, `--read-only`, `--constraint`, `--out-of-scope`,
`--readme-file`, `--checkpoint-file` all exit 2 at argparse before any
gate runs (nothing consumed). Pinned: `--write` and `--checkpoint-file`
as expectedFailures (they are the two the reproductions above need);
the rest as one passing `subTest` sweep. The comment on
`constraints=[]`/`out_of_scope=[]` calls the narrow surface deliberate
"until the use case argues for more"; paths 2 and 5 are the use case.
"Old syntax" almost certainly names this: the operator typed a pack
flag at handoff. Modernizing touches `p_handoff` and the
corresponding `cmd_handoff` wiring per flag; each is a mirror of
pack's existing plumbing.

### 7. Lead 4 — NOT reproduced

The handoff-built manifest stamps `work_class: "mixed"`,
`checkpoint: null` (unconfigured), `checkpoint_scope_admitted: false`,
no `checkpoint_waived`, and a `base_files` map whose per-file hashes
equal `git show HEAD:<path>`; a whole-tree handoff session's response
applies with the base-drift gate satisfied. Pinned as a passing test.
The manifest is not old; the argv is.

## Recommendation: modernize

**Modernize, in one session, in this order: 5 (forecast inheritance),
1 (disjointness gate), 4 (`forecast_declared`), 2 (`--checkpoint-file`
or the `caller`-aware remedy), 6 (the flag family as far as 5 and 2
need it).** Retire with a tombstone only if the desk decides the
bailout → handoff loop itself is dead.

Reasoning:

- Every break is a *shared* gate or value called with stale arguments.
  Nothing here needs new machinery: the disjointness gate, the
  `forecast_declared` parameter, `read_session_scope`,
  `locate_and_read_checkpoint_file`, and `read_includes` on the
  blindness gate all exist and are exercised by pack's suites. The
  modernization is mostly deletion of comments that assert the old
  world plus one argument per call site. Path 5 is the largest and it
  is ~10 lines.
- The reproductions are already the modernization's acceptance tests:
  six `expectedFailure`s that flip to unexpected-success one by one as
  each path is re-based, with pack-side controls beside them asserting
  the parity target. Session B strips a decorator per fix.
- Against retirement: `bale handoff` is the only consumer of
  `handoff.md`'s reading plan and the only path that populates
  `depends_on.previous_response` (the lineage chase, `warn_repeat_bailout`,
  and the stats linkage rows all key on it). Retiring the verb orphans
  the bailout artifact contract (TARBALL.md §5.6–5.8) or pushes its
  work onto the operator as a manual repack — the friction CLAUDE.md
  §1 names as the system's one failure source, and the reason the
  reading-plan pre-pack was written in the first place.
- The one honest argument for retirement is that under the modern
  orchestration shape bailouts are re-planned at the desk rather than
  re-run, so handoff's "same goal, fresh budget" premise may itself be
  design-era. I don't have the data to say (no telemetry corpus was
  shipped, and `stats` rows for handoff-origin sessions would answer
  it). If the desk has it and the answer is "no handoff has succeeded
  since 0.4.1", retire. Otherwise the cost asymmetry favors
  modernizing.

Absorbed rows, one sentence each: **row 71** — handoff allocates its
sid (`peek_session_id` → `next_session_id`) and never resolves one, so
a `--sid` on it could only be the retry-style vetting flag ("must
equal the bailout manifest's `responds_to`"), and `bale open`'s
bundle-driven pack has the same shape; a shared vetting-only `--sid`
is cheap and adds nothing to either until several bailouts sit in the
inbox at once — not worth session B's budget unless that is now
common. **The `gather_files_for_pack` rider** — the function has no
`verbose` kwarg today (only `walk_for_pack` does), so handoff's
`--verbose` streams the build trail but not the reading-plan filter's
per-file drop *reasons*; the candidate and included lists are logged
(so the dropped set is derivable by subtraction), but the `why` of
each drop — typo, untracked, secret pattern, unsafe path — is the
verbose-only `_drop` trail that `gather_files_for_pack` cannot
switch on; threading `verbose` through it to `walk_for_pack` is a
3-line rider for session B, and it turns the drop list into
something an operator can actually audit.

## Test structure

- `tests/test_handoff_fixture.py` carries the shared fixture; it
  matches the `test_handoff_` prefix so the bare import resolves under
  direct runs the same way `harness` does (precedent:
  `test_checkpoint_file_flag.py` importing `test_per_sid_checkpoint`).
  It defines no tests (validation asserts "Ran 0 tests" on it) and no
  class-level decorators (validation asserts that too — the board-75
  inheritance trap). Every `expectedFailure` is per-method.
- I did not refactor `test_handoff_happy.py` onto it. Its three cases
  are the baseline the brief measures the gap against; the diff stays
  purely additive and the reproduction does not depend on a refactor.
  Listed in `deferred`.
- Each `expectedFailure` was run with the decorator neutralized to
  confirm it fails at the *intended* assertion (the handoff's exit
  code or the apply's), not at a fixture step; the pack-side controls
  are plain tests precisely so a fixture regression fails loud instead
  of hiding behind an expected failure.
- Runtime: the four handoff suites run ~13s, under the default tier;
  no `@slow` gate.

## Claims

Four checks are `observed`: `validation.sh` was rehearsed in a
staging-shaped copy of the shipped `context/` (files overlaid,
manifest placed at `.bale-manifest.json`) and exited 0 with every
claimed check `[agree]`. Full discovery is `predicted` and gated
behind `--slow`, per the board-75 correction: I observed the four
handoff suites plus `test_readonly_pack.py` and
`test_blind_checkpoint.py` (49 tests) in the shipped copy; I could not
run `test_checkpoint_file_flag.py` there because it imports
`test_per_sid_checkpoint`, which the request did not ship
(`includes_missing`), and I have not run the other ~780. The one
prediction risk I can name: a repo suite that asserts every
`tests/test_*.py` has an `if __name__ == "__main__"` block would trip
on the fixture module (it has none, deliberately). I found no such
suite in the shipped hashes' names, but it is a prediction.

## Surprises

- The two unpredicted classes both come from one sentence in
  `cmd_handoff` — "the read set and the forecast coincide by
  construction" — which is a correct description of ADR-0007 and a
  false one of ADR-0015. Everything downstream of that sentence
  (`forecast_declared`, `read_includes=None`, the `["."]` fallback
  becoming the forecast) follows from it.
- Refusal text is shared across callers on both checkpoint gates, and
  in both cases the shared text names a remedy handoff cannot take.
  The v0.4.10 remedy-wording pass ("name their real remedy and their
  real actor") only audited pack's invocations.
- `open_sessions()` is called in `cmd_handoff` *before* the tarball is
  opened, so a bailout that would be refused for a bad shape is
  masked by the open-session refusal — the operator sees only the
  first gate. Not a break; worth knowing when reading a report.

- The response-side provenance echo (`feedback.mechanical.provenance`,
  `additionalProperties: false`) does not admit `base_files`, which
  every bale-built request has stamped since board 41 and which this
  request carries. "Echoed verbatim" is therefore impossible for a
  modern request; I echoed the block minus `base_files` to validate.
  Schema lag, desk-owned (`schemas/` is out of my forecast); a line
  for the next schema session.

## Proposals

- **What:** a `caller` kwarg on `checkpoint_resolved_preflight`
  mirroring the blindness gate's, so the remedy sentence names only
  what the caller offers. **Why:** path 2's misroute is independent of
  whether handoff ever gains `--checkpoint-file`, and it is the
  cheapest fix in this file. **Scope hints:** `bin/bale_pack.py`
  (the gate and the refusal string), both call sites; session B.
- **What:** a `stats` drill-down row for handoff-origin sessions
  (`command == "handoff"` in `persist_pack_session`) with their
  outcome distribution. **Why:** the modernize-vs-retire call turns on
  whether the verb has produced a landed session since 0.4.1, and the
  registry already records the origin command. **Scope hints:**
  `bin/bale_stats.py`; independent of session B, useful before it.
- **What:** when a request ships `test_checkpoint_file_flag.py`, ship
  `test_per_sid_checkpoint.py` beside it. **Why:** the former is
  unrunnable without the latter, which cost this session its one
  shipped `{sid}` precedent and is the same `includes_missing` shape
  the board-75 retry recorded. **Scope hints:** desk forecast
  authoring; no code.
