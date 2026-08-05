# Notes — 2026-08-05-auto-sweep-009

## The guard interaction (the brief's explicit question)

Verified against the archive-dir-005 carve-out: **the carve-out needed
no extension, and the sweep runs entirely post-guard-window** — the
dirty-tree guard judges the tree before any git mutation, and every
sweep trigger fires only after the parent event's git work is durably
complete. But the verification surfaced something the brief's framing
didn't anticipate: rollback and `--undo` had to *join the trigger set*.
Once a sweep has committed a sid's telemetry record, the record is
tracked; rollback's own telemetry append then makes it a *modified
tracked* file, which the carve-out deliberately refuses (untracked-only
by design). Without a sweep at the rollback trigger, the first swept
rollback would strand a modified record and the `--undo` toggle would
refuse without `--stash`. With it, each clean rollback/undo commits its
own append immediately and the toggle stays clean — suite-pinned in
`RollbackToggleTest`. A *skipped* sweep still leaves the record
modified-tracked and the next guard run refuses loudly; that is the
manual-sweep prompt, and I left the conservatism intact rather than
widening the carve-out to modified files. Prose in BALE.md §9.2 step 3.

## Trigger enumeration (the judgment the brief delegated)

Sweeping: apply's applied / walkthrough-revert / bailout outcomes,
`bale revert`, everything through `close_session_with_record` (unlock,
pack's supersession close, pack's read-only sweep close), unlock's
crash-debris record, and rollback's `rolled-back` / `re-applied`. Not
sweeping: held, the two refusal outcomes, `rejected`, and
clarifications — the session continues in each, and the record rides
to its eventual closure, where the sweep picks up every accumulated
attempt in one commit. The commit-message event is the outcome word,
except through `close_session_with_record`, where I stamp the
`closure_reason` (`abandoned`, `closed-read-only`,
`superseded-by-split`, `crash-debris`) — more informative than the
uniform `unlocked` outcome those closes share.

## Where the sweep commit lands

On the **current branch** — including after a checkout-untouched merge
(operator on another branch, ref advanced via update-ref). That is
where the manual dance this mechanizes would have committed the
untracked files, since they are working-tree files of the current
checkout; committing them to a branch the checkout isn't on is not
something git offers cheaply. Worth a deliberate look on review: if
you'd rather the sweep *skip* when the checkout is off the integration
target, that's a two-line predicate in `sweep_commit`.

## Malformed-key posture, split by site

On the apply pipeline the key resolves at pre-flight through the
strict accessor beside `archive_dir` — a non-bool typo refuses before
staging, never post-merge (suite-pinned for archive_dir; sweep rides
the same resolve). On the commands with no such pre-flight (unlock,
revert, rollback, pack's closes), the strict accessor still fires but
inside `sweep_commit`'s never-fail wrapper: the fatal error prints,
then the sweep degrades to a loud skip naming the manual sweep as
successor — because at that point the closure/revert has already
durably happened and exiting non-zero after the fact would convert a
completed operation into a failure. It's a deliberate asymmetry; flag
it if you want refusal-before-action on those commands too (it would
mean resolving the key at each command's start).

## "The config surface row"

Shipped BALE.md has no config-key table; the canonical discoverable
surface is the wizard (§3.6) and the internals doc, which isn't in
this tree. I read "the config surface row" as the `APPLY_VALUES` entry
(the trio's row in code) plus the §8.8 behavior prose beside
archive_dir's, which is where archive_dir itself is documented in the
shipped doc. If you meant a row somewhere in bale-internals.md §4,
that edit rides the next session that touches the internals doc — out
of this tree's surfaces per the constraints.

## Output shape

The required loud line (`sweep: committed <n> file(s) as <short-sha>`
/ `sweep: nothing to commit` / the skip form) is emitted by
`sweep_commit` itself via `log()`, so it reaches the terminal and the
session log at every trigger, and lands on stderr under `--json` per
the stream discipline. A banner *row* was added only to the applied
banner (the archive-row precedent); unlock/revert/rollback carry the
log line without a new row — minimal v1, easy to extend. One adjacent
fix: the applied banner's archive row said "(uncommitted)", which
became false on its face when the sweep two lines up had just
committed the copies; it now reads "(committed by sweep)" in exactly
that case and is byte-identical otherwise.

## Deferred, with reasoning

- **Telemetry stamp of the sweep result.** Chicken-and-egg: the sweep
  commits the record written moments before, so stamping the sweep's
  own result into that record would mean rewriting it after the
  commit (and re-committing, or leaving it dirty — either breaks the
  clean-tree invariant the feature exists for). If v2 wants it, the
  natural shape is stamping the *next* attempt, or a sweep sidecar.
  Successor: the stats/telemetry session below.
- **Additive `--json` sweep key.** Minimal-at-v1 per the brief; the
  key list's one home is `format_apply_json`'s docstring and I didn't
  touch it. Successor: the same follow-up session.

## Proposals

- **What:** an additive `sweep` object in `format_apply_json` (and the
  unlock/revert json siblings), plus `bale stats` read-side sweep
  coverage once a stamp exists.
  **Why:** an orchestrating operator dispatching on the json line
  currently can't see whether bookkeeping landed — it's stderr-only.
  This session deliberately kept the json contracts untouched
  (minimal-at-v1); the seam is clean since `sweep_commit` already
  returns the structured dict the key would serialize.
  **Scope hints:** `bin/bale_report.py` (key-contract docstrings),
  `schemas/telemetry-record.schema.json` if a stamp lands; only after
  this session merges.
