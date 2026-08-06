# Notes — 2026-08-06-sweep-json-stats-002

## The stamp decision: reasoned deferral (charter option 3)

The charter asked me to pick the next-attempt stamp, the sweep
sidecar, or make the case that neither earns its keep. I'm making
that case, and per your conditional the stats read side defers with
it — nothing here builds a reader with no records to read.

**The next-attempt stamp has near-zero coverage.** Telemetry records
are per-sid files that gain attempts; a "stamp the next attempt"
design only works where a next attempt exists in the same record.
But the sweep fires exclusively on closing events — applied,
reverted, unlocked, bailout, crash-debris — and every one of those
is terminal for its sid's record. The one intra-sid chain that gets
a later attempt (HOLD → retry) doesn't sweep on HOLD, so there is no
sweep result waiting to be stamped when the retry lands. The shape's
coverage rounds to zero on the actual trigger set; stamping into the
*next session's* record instead would be cross-sid pollution that
per-sid aggregation can't use.

**The sidecar breaks the invariant it must honor, precisely where
stats wants it most.** A sidecar written after the sweep commit is
itself bale-written bookkeeping left untracked — the exact state the
feature exists to eliminate — and nothing later sweeps it. The
committed form could theoretically be folded in with an
`--amend` dance (commit the record, write a sha-less sidecar, amend),
but the skip paths have no commit to amend: a detached HEAD or
identity failure would strand the sidecar untracked exactly when the
sweep already failed to keep the tree clean, compounding the mess.
And skips are the rows a longitudinal signal cares about most — a
stamp design that loses them where they occur isn't worth its
complexity.

**What tips it: this session's own deliverable covers the
operational need, and the durable trail already exists for the rest.**
The json `sweep` object gives an orchestrator event-time dispatch on
committed/nothing/skipped, with the skip reason in `detail`. For
longitudinal committed-sweep data, the git log is already a
queryable, durable record — `git log --grep '^\[bale sweep '` yields
sid, event, timestamp, and files per commit, no schema change needed.
The genuinely unrecorded residue is skip *rates* (skips live only in
session logs), and I'd wait for evidence that anyone wants that
number before paying a schema migration and an invariant contortion
for it. Re-trigger I'd propose: the first time someone actually goes
looking for sweep-skip frequency.

Consequences in this change set: `schemas/telemetry-record.schema.json`
untouched (so no `test_schema_embeds.py` refresh — the pin's
land-with-the-change rule is satisfied vacuously), `bin/bale_stats.py`
untouched, no new stats fixtures.

## Decisions to ratify

- **Null means "no sweep ran," collapsing disabled and
  no-sweep-event.** The `sweep` key is null both when `[apply].sweep`
  is unset/false and when the outcome performs no sweep (held,
  clarification, dry-run, the refusals). This mirrors the `archive`
  key's posture and keeps the trigger set out of the json contract —
  a consumer distinguishing the two cases is asking a config
  question, not an outcome question. If that distinction ever
  matters, a `{"configured": false}` form per the checkpoint key's
  precedent is an additive upgrade path.
- **One normalizer, one home.** `format_sweep_json` in
  `bale_report.py` normalizes `sweep_commit`'s return to stable keys
  (`sha` null / `files` [] outside the committed form);
  `format_apply_json`'s docstring owns the sub-object's key list and
  the unlock/revert docstrings point there. Call sites pass the raw
  dict; renderers normalize — so the shape has exactly one producer.
  On the skipped form `files` is `[]` even though files were left
  behind: `sweep_commit`'s skip return doesn't enumerate them, and I
  wasn't going to invent data the function doesn't report (the count
  and names are in the log line `detail` echoes).
- **`close_session_with_record` returns a 3-tuple.** The sweep
  result had to cross that function boundary to reach unlock's json.
  Pack's two callers (supersession, read-only sweep) discard the
  third element — pack's own json report has no sweep key this
  session, deliberately: the goal named apply/unlock/revert, and
  pack's read-only sweep can close *several* sids, which wants a
  list-shaped key worth its own small design pass (see Proposals).
- **The debris record's sweep rides `debris.sweep`,** not the
  top-level key, following the docstring's existing rule that the
  debris record's facts ride under `debris`. The top-level key stays
  null on the no-op.
- **Rider 2 landed exactly at the relaxed seam.** Only the
  narrowing-remedy sentence swaps on `caller`; diagnosis,
  ordinary-update-path, and flag-successor text remain byte-shared.
  The pass-through parameter lives on the shared gate
  (`checkpoint_blindness_preflight`, default `"pack"`), so pack's
  call sites are unedited and only `cmd_handoff`'s call names itself.
  The B1 suite's existing assertions needed **no loosening or
  splitting** — they pin the shared diagnosis and flag lines, which
  didn't change — so the deviation-with-reasoning you provisioned
  for wasn't needed; I *added* assertions pinning both remedy
  renderings (each present on its caller, absent on the other).

## Where to look on review

- `format_sweep_json` + the three renderer docstring additions in
  `bin/bale_report.py` — the key contracts are the durable surface.
- The applied path in `bale_apply.py` already captured
  `sweep_result` for the banner; the bailout and walkthrough-revert
  paths captured it for the first time. Verify I didn't disturb the
  banner logic (I didn't touch it; the diff should show only the
  capture and the json pass-through).
- The `test_unlock_json_skipped_object_names_the_reason` test pins
  the machine-readable skip — the case that motivated putting
  `detail` in the object.

## Test-runtime note

`validation_will_run` includes full discovery (~65s in my
environment), which pushes total wall time near the 2-minute target
but under it. I kept it ungated: this change touches three shared
json surfaces and a shared refusal formatter, and the collateral
sweep is where a regression would hide.

## Proposals

- **What:** a `sweep` key on pack's `--json` report covering the
  read-only sweep's closes (list-shaped: the sweep can close several
  sids per pack) and the supersession close.
  **Why:** this session threaded the sweep result through
  `close_session_with_record` for exactly this reason — pack's two
  callers now hold the result and discard it. The remaining work is
  key design (a list of per-sid objects) rather than plumbing.
  **Scope hints:** `bin/bale_pack.py` (the two call sites,
  `format_pack_json`'s contract in `bin/bale_report.py`); after this
  session merges.
- **What:** a `bale stats` sweep view derived from the git log
  (`[bale sweep <sid>] <event>` commit messages) if longitudinal
  committed-sweep data is ever wanted.
  **Why:** it needs no schema change and no invariant contortion —
  the commit trail already carries sid, event, time, and files. Only
  build it on demand; and if skip *rates* are the actual question,
  that's the re-trigger for revisiting the stamp with fresh eyes,
  not for this derivation.
  **Scope hints:** `bin/bale_stats.py`; independent of everything
  above.
