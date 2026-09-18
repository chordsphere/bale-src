# Notes — 2026-09-18-board-107-supersedes-clean-tree-004

## What I found

Your reproduction holds on the 0.4.35 bytes exactly: ` M` on the
parent record, `??` on the child's, and `[bale sweep <parent>]
superseded-by-split` landing before the child's `bale: per-session
checkpoint` commit. The ` M` diff is one line — the
`"superseded_by": "<child>"` key that `stamp_superseded_by` adds to the
closure attempt. Everything else in the record was already committed.

## The fix

`cmd_pack` now calls a new pack-side helper,
`sweep_superseded_by_stamp`, immediately after `stamp_superseded_by`.
It hands `bin/bale`'s `sweep_commit` (unchanged) exactly the one path
the stamp rewrote, under the event `superseded_by <child>`, so the
commit reads `[bale sweep <parent>] superseded_by <child>` — inside
the §8.8 message family, and naming the child in the log so
`git log claude/telemetry/` shows the lineage edge. Every sweep rail
comes free: pathspec-only, loud either way, never fatal, and with the
key unset or false `sweep_commit` returns None with no output — so that
path is byte-identical to today (two tests pin it: false and unset).

On a failed stamp (stamper already logged it loudly) the helper sweeps
`[]`, which prints `sweep: nothing to commit` — the same
`[x] if x else []` idiom `close_session_with_record` uses, so the event
is never silently skipped.

**Why two sweep commits rather than one.** The brief allowed either
shape; I chose a second commit over moving the close's sweep later.
One combined commit would need a `sweep=False` knob on
`close_session_with_record` in `bin/bale` (out of forecast), and it
would regress the accepted-abort window: a gate refusal against a
second open session, a cap refusal, or an editor abort all happen
after the close and before the child sid exists. Today the closure is
committed in those cases; a deferred sweep would leave it uncommitted.
So the closure sweeps at its event and the stamp sweeps at its event.
The cost is one extra small commit per accepted supersession. Ratify
or redirect.

`bin/bale` is untouched, as you expected. Nothing is shipped outside
the forecast.

## Registry rider — does it still reproduce?

**Not as written, on these bytes.** `close_session_with_record` writes
the closure record at step 4 and sweeps it at step 5, and the rehearsal
shows the sweep commit carrying the full closure attempt. The
log-ordering evidence the rider cites — the sweep-commit line printing
before the closure-record line — is still visible, but it's a reporting
artifact: the `superseded <sid> (closure record: …)` line is logged by
`_resolve_supersession` *after* `close_session_with_record` returns, so
it necessarily follows the sweep line. It is not a write-after-sweep.

My read is that the dirt the 2026-08-13/14 sitting hit was this same
stamp. The stamp (v0.3.23) predates the sweep (v0.3.32), so every
swept supersession since then has left exactly this ` M`. That's
inference from the code and version history, not from the sitting log,
which I don't have. The tree-clean test the rider asked for is in
either way.

## Tests

Five new cases in `tests/test_supersession_pack.py`:

- `test_accept_leaves_tree_clean_checkpoint_recipe` follows your recipe
  verbatim (`{sid}` base, sweep on, parent via `--checkpoint-file`,
  `opened` committed, pty `y`). It asserts no tracked dirt (the child's
  own `??` allowed), the HEAD record equals the working tree and carries
  `superseded_by`, and the commit order: stamp sweep, then child
  checkpoint, then closure sweep.
- `test_accept_leaves_tree_clean_plain_config` covers sweep on with no
  checkpoint base and no hand-commit of `opened`. The defect isn't
  checkpoint-specific, since the close's sweep adds the record itself.
- `test_idempotent_rerun_leaves_tree_clean`: the re-stamp is committed,
  and HEAD names the completing child.
- `test_sweep_false_commits_nothing` / `test_sweep_unset_commits_nothing`:
  no `sweep:` output, no sweep commit, stamp still on disk.

The first three **fail on the shipped `bale_pack.py`** with the ` M`
line. `validation.sh` re-proves that in staging when HEAD holds the base
bytes (sha-checked), and skips loudly otherwise. The other two pass on
both, which is the point.

Full `unittest discover` shows the same 5 pre-existing
failures/errors before and after (all environmental: the repo's own
`bale.toml` and `claude/changelog/` aren't in the request context).
The fixed tree runs +5 tests. Under `BALE_TEST_SLOW=1`, the auto-sweep,
read-only, checkpoint-file, per-sid, closure-telemetry,
pre-answered-intents, pack-guards, and write-forecast suites are
all green.

## Bumpless-under

No `bin/VERSION` change and no version tag added or removed in either
file. `validation.sh` asserts both relative to this response's
`changes[]`, plus that the touched files' highest tag is ≤ the staged
`bin/VERSION`.

## One thing to look at on review

The comment on `depends_on.superseded_session` in `cmd_pack` still says
the parent's closure record "carries no successor pointer". That has
been stale since v0.3.23's reverse stamp. I left it alone because it's
unrelated to this fix and rewording it widens the diff. Flagging it
here instead.

## Proposals

- **What:** Surface the stamp sweep (and the close's sweep) in
  `bale pack --json` as an additive `sweep` key, mirroring apply's and
  unlock's.
  **Why:** Pack discards the close's `sweep_commit` result today
  (`telemetry_rel, _, _ = …`), and the new helper's result has no json
  home either. So tooling reading pack's one JSON line can't tell
  whether the supersession's bookkeeping was committed or skipped.
  **Scope hints:** `format_pack_json` in `bin/bale_report.py`
  (sibling-held by 47b this wave), then a one-line pass-through in
  `cmd_pack`. Only after 47b lands.

- **What:** A sentence for BALE.md §8.8's trigger list, for 99b's
  true-up: "…pack's session closes (the read-only sweep and the
  supersession close, §7.2), including the supersession's
  reverse-lineage stamp on the parent record, swept as its own
  `[bale sweep <parent>] superseded_by <child>` commit once the child
  sid exists…"
  **Why:** §8.8 enumerates the owned-file trigger moments. The stamp is
  now one of them, and the prose shouldn't lag the code.
  **Scope hints:** `BALE.md` §8.8 "Auto-sweep commits" paragraph.
  Prose only.
