# notes: 2026-11-14-dossier-says-more-002 (bale 0.4.62)

All six outcomes are built, and so is the release. Every path I touched is
inside the forecast (BALE.md, bin, claude/changelog,
claude/context/bale-internals.md, schemas, tests), so there are no
departures to admit. The whole unit suite ran clean in my sandbox:
2227 tests, 48 skipped, about 12 minutes (2208 at 0.4.61 plus the 19 new ones). The default validation.sh runs in about 80 seconds. The
whole suite sits behind `--slow` and is claimed `untested`, because a
default apply skips it.

## Decisions to ratify

- **Open read-only sessions leave the rates.** The brief left this to
  me. `is_read_only` now names a session read-only from its pack on.
  So an open read-only session drops out of the classed membership: the
  class rows, the closure mix, packers and doc_epochs. That is where a
  closed one has always been. I kept `members.in_flight` and
  `corpus.in_flight_sessions` exactly as they were. An open read-only
  session still counts there, and the work_class filter still reaches it
  through its resolved class, as it did when it sat in the membership.
  The visible effect on a live repo: while a planner sitting is open,
  `corpus.sessions` and the class rows are one lower than in 0.4.61, and
  `read_only_sessions` is one higher.
- **The read-only signal is the first `opened` attempt** with
  `scope_kind` "write-forecast" and `scope` `[]`, as the sitting
  guessed. It is the first one because a second `bale open` of an open
  bundle appends another `opened` attempt (command `open`). Every
  opening call site hands the builder a list (`resolve_write_forecast`,
  and handoff's resolution), so `[]` there means a declared empty
  forecast, never None turned into a list. I checked both sites.
  `persist_pack_session` itself still turns a `scope=None` into `[]` on
  the opened attempt. No caller passes None today, but that collapse is
  the one way this reading could lie.
- **Read-only wins over crash-debris.** That precedence is older than
  this change (`crash_debris` excludes read-only). It now applies to one
  more case: a read-only session that ends as crash debris counts under
  read-only, where 0.4.61 counted it under crash-debris.
- **`bale_version` is one top-level key on every attempt.** I did not
  repeat it inside the opened attempt's `provenance`, which the sitting
  guessed. That block copies the request manifest's provenance, and the
  attempt-level key already says the same thing for every command.
  `install_bale_version()` reads bin/VERSION next to the module rather
  than importing it from `__main__`, so the builder works in the unit
  suites too. Under bin/bale the read cannot miss, because bin/bale
  exits first when that file is unreadable.
- **`claimed_checks` lives in the attempt's `validation`**, built by
  `claimed_checks_counts` on top of `summarize_claimed_checks`. It is
  the same function, fed the same inputs, as the line apply prints, so
  the two cannot drift. When there are claims but validation printed no
  claims block, I record `ran: null, disagreements: []`. That matches
  what the walk prints ("how many ran is unknown") and keeps bale from
  naming disagreements it never saw. With no claims at all it reads
  `{0, 0, []}`.
- **`corpus.hold_classes` always has all four words** (0 when none).
  Beside it I added `corpus.held_attempts`, so a held attempt that fits
  no class shows up as the gap and is never put in a class by guess.
  Both count the filtered membership's response attempts, the same unit
  as `response_attempts` beside them.
- **`members.sessions` is the whole loaded corpus.** It sits outside
  `--since` and `--work-class`, like `corpus.records`. The human report
  leaves it out of the "corpus members" block, since that block would
  otherwise print every sid on one line.
- **Human renderings.** As the sitting guessed: the dossier prints
  `; hold class <word>` after a held attempt's line, a `bale:` line for
  each stamped attempt, a `claimed checks:` line, and `bale version` and
  `self-reported` summary rows. The stats summary gains a `held` row,
  e.g. `3 attempts (checkpoint-defect 1, checkpoint 1, no class 1)`.

## Where a null HOLD class can come from

I found no way for `bale apply` to write one. The class reads null on a
held attempt with no recorded validation exit code, on a configured
checkpoint stamp with no integer `exit_code`, or when both scripts
exited 0. As far as I read bale_apply, a held attempt always has a
validation exit code, and both scripts exiting 0 produces a PASS. Only a
hand-edited or damaged record reaches these shapes. The tests pin all
three as null.

## Places to look on review

- `bin/bale_stats.py` `compute_stats`: the block that adds open
  read-only sessions back into the in-flight count. It is the one
  subtle part.
- `tests/test_stats_aggregation.py`: I extended its exact pin on the
  corpus dict. That is the only existing test I changed. The fixture
  corpus itself is untouched.
- `tests/test_dossier_says_more.py` has two end-to-end cases (a
  read-only pack, and a pack plus apply with the brief's four-claim
  example). Neither is gated behind `BALE_TEST_SLOW`, because together
  they take a few seconds.

## Proposals

- **What:** publish HOLD_CLASSES in `bale contract` as a closed
  vocabulary, beside the others it lists.
  **Why:** the dossier and the aggregate now emit those four words as
  values, and a consumer like the office should read the list from the
  install instead of copying it from the brief.
  **Scope hints:** bin/bale_report.py's contract declarations and
  tests/test_contract_verb.py.
- **What:** add a fixture to the stats corpus that is written after
  the release (an opened attempt with `scope_kind`, a `bale_version`, a
  `claimed_checks`).
  **Why:** the shared fixture corpus has no `scope_kind` at all, so the
  whole-corpus expectations never exercise the forecast-era readings.
  This session tested them over synthetic corpora instead.
  **Scope hints:** tests/fixtures/stats_corpus/ and the whole-corpus
  pins in tests/test_stats_aggregation.py, which would move with it.

## Walkthrough

### What changed

- **bin/bale_stats.py, read-only detection.** `is_read_only` is true on
  a `closed-read-only` closure, as before, and now also when the
  session's first `opened` attempt recorded an empty write forecast.
- **bin/bale_stats.py, new readers.** `attempt_hold_class` (the four
  HOLD classes, read from exit codes), `attempt_bale_version` and
  `session_bale_version`, `attempt_claimed_checks`, and
  `session_self_reported_value` (which keeps None).
  `session_self_reported_count` now wraps that last one and still
  returns 0 for "not reported".
- **bin/bale_stats.py, the aggregate.** `corpus.held_attempts`,
  `corpus.hold_classes`, and `members.sessions` are new.
  `members.read_only` now names open read-only sessions too.
  `members.in_flight` is unchanged.
- **bin/bale_stats.py, the dossier.** The record gains `bale_version`
  and `self_reported`. Each attempt gains `hold_class` and
  `bale_version`, and its validation view gains `claimed_checks`.
- **bin/bale_report.py, the write side.** Every telemetry attempt now
  carries `bale_version`, and every validated attempt carries
  `validation.claimed_checks`.
- **bin/bale_report.py, the renderers.** The dossier and stats reports
  print the new facts, and both JSON key-contract docstrings list the
  new keys.
- **schemas/telemetry-record.schema.json.** The two new attempt fields,
  both additive.
- **BALE.md 5.6 and 8.9, claude/context/bale-internals.md.** The docs
  say what the code now does.
- **tests/test_dossier_says_more.py** (new), and one pin extended in
  tests/test_stats_aggregation.py.
- **Release.** bin/VERSION is 0.4.62, and claude/changelog/0.4.62.json
  is its record.

### Why

- Slip 4: a read-only session opened from a bundle read
  `read_only: false` until it closed, because only the closure said so.
- Slip 5: no record carried bale's own version, so the office had to
  print "not on bale's dossier" for it.
- Slip 6: no JSON surface listed every session, so a pruned outbox
  would hide sessions from the office's ledger.
- Slip 3: the aggregate summed the self-reported counts, but the
  dossier did not show one session's own figures.
- Slip 2: `cause` turned out to be a refusal's first error line, not a
  HOLD class, so the HOLD class is new, using the four words the
  occupant ratified.
- The fold-in from the first round: apply printed "N of M checks ran"
  but recorded nothing, so the count was lost after the walk.

### How to explain each piece

- **Read-only while open.** "A session packed with nothing to write is
  read-only from the moment it's packed, not only once it's closed. It
  still shows as open while it's open."
- **bale's version.** "Every event bale records now says which bale
  wrote it. Older records say null rather than borrow the version the
  worker copied from its request."
- **Every session.** "The aggregate now lists every session id it read,
  so you don't have to piece the list together from the outbox."
- **Self-reported counts.** "The dossier shows the session's own light
  block and paste-carried round counts. Null means it never said, which
  is different from zero."
- **HOLD class.** "Each held attempt says why it held: the checkpoint
  objected, validation failed, both did, or the checkpoint itself
  broke. It's read from the exit codes, so old holds classify too."
- **Claimed checks.** "The 'N of M checks ran' line apply prints is now
  saved with the attempt, so you can read it back later."

### Questions a reviewer will ask

- *Why exit codes and not `validation.state`?* On a held attempt,
  `validation.state` is the combined verdict and reads HOLD even when
  validation.sh exited 0. The exit codes are the only per-script facts.
- *Does a 0.4.61 record still read the same?* Yes. Every existing key
  keeps its meaning. The new keys read null on old records, except
  `hold_class`, which classifies from facts old records already hold,
  and `read_only`, which can now turn true for an open read-only
  session.
- *Why is a read-only session still "in flight"?* An open session is
  in flight whatever its kind. The brief pins `members.in_flight` as
  unchanged.
- *Can `claimed_checks` and the printed line disagree?* No. Both come
  from `summarize_claimed_checks`, fed the same claims and the same
  captured validation output.

### A hand test

1. In a scratch repo with 0.4.62 installed, run `bale pack "look
   around" --slug look --include README.md --read-only --no-readme`.
2. Run `bale stats --sid <that sid>`. The status row reads
   `in-flight [read-only]` and the `bale version` row reads 0.4.62.
3. Run `bale stats --json` and check that `members.read_only`,
   `members.in_flight` and `members.sessions` all name the sid.
4. Pack a normal session. Apply a response whose validation.sh exits 1,
   then run `bale stats --sid <sid>`. The held attempt's line ends
   `; hold class validation`, and the summary's `held` row in
   `bale stats` reads `1 attempt (validation 1)`.

## Handbook

### bale-src

- Since 0.4.62 every telemetry attempt bale writes carries `bale_version`, the running install's bin/VERSION; attempts written earlier lack it, and the dossier reads null for them rather than the worker's provenance echo.
- Since 0.4.62 `bale stats` reads a session as read-only from its pack on: `is_read_only` is also true when the first `opened` attempt records scope_kind "write-forecast" with scope `[]`; an open read-only session is in `members.read_only` and `members.in_flight` and out of every rate.
- Since 0.4.62 `bale stats --json` carries `members.sessions` (every loaded sid, sorted, outside both filters) and `corpus.held_attempts` with `corpus.hold_classes`.
- Since 0.4.62 each dossier attempt carries `hold_class`: checkpoint-defect, both, checkpoint or validation, read from the checkpoint's and validation.sh's exit codes, null when the attempt is not held; held attempts from earlier releases classify too.
- Since 0.4.62 every validated attempt's telemetry carries `validation.claimed_checks` `{claimed, ran, disagreements}`, the counts apply prints as "N of M checks ran", and the dossier shows them; `ran` is null when validation.sh printed no claims block beside a non-empty claims map.
- Since 0.4.62 the dossier's `record.self_reported` carries `light_blocks` and `paste_carried_rounds` by the aggregate's latest-carrier rule, null when no attempt reports them.
- A telemetry attempt's `cause` is a refused attempt's first error line, written on rejected and relay-refused attempts since 0.4.41; it is not a HOLD class.
- The whole unit suite runs clean in a worker sandbox at 0.4.62, with the new tests/test_dossier_says_more.py: 2227 tests, 48 skipped, about 12 minutes; that session's default validation.sh (the targeted stats, telemetry, release and doc modules) takes about 80 seconds.

## Structure

- title: Fix bale-src for the slips about bale, in eleven sessions
- size: high
- goal: Land the fixes to bale-src for the slips about bale in the office's suggestion box, one release per session, in the ratified order
