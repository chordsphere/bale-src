# Row 45 — first-wave upward report

Session `2026-09-24-board-45-close-008`, read-only close of the arc opened by
`2026-09-23-board-45-hostile-repo-design-010`. Corpus: the seven ratified
`stemwell` sessions' telemetry and notes, plus the abandoned seed v1 record.
Two facts came from the operator by light block (probe round trip, shell
locale); everything else is from the pack.

## Partition

**Landed (7).** Seed v2 (23 paths, PASS/PASS, one `[n/a]` row); wave1
trailing space (PASS/PASS); wave2a `prune` (HOLD, then PASS/PASS on retry);
wave3 codec regen (PASS/PASS); wave5 gzip ingest (PASS/PASS); wave2b
`export` (PASS/PASS); wave4 `report --json` (PASS/PASS). Checkpoint PASS on
all eight apply attempts, the HOLD included.

**Ratified at apply (flagged worker deviations, all admitted by landing).**
wave1 edited `test_report.py` to remove the two `.rstrip()` masks; wave2a's
strict not-found rule and unrequested `--dry-run`; wave2b reusing
`report.load_state_records` and writing dest directly; wave3's
predicted-not-observed tally assertion; wave4's un-sorted JSON path and
`total`-collision error; wave5 housing the gzip helper in
`commands/ingest.py` and case-sensitive suffix detection. Four admitted
out-of-forecast paths (`prune.py`, `test_prune.py`, `export.py`,
`test_export.py`), each by prompt.

**Escalated (to S6, via the proposals below).** Read-side coupling, which
ADR-0015 cannot name; the two design-desk defects (v1 wording refusal;
`--write .` refused by the blindness gate); hot reads missing from include
sets; new-file admission cost; probe timing not recorded.

**On-watch.** The five parked worker proposals (locale-independent
ordering; `tomllib` vs the 3.10 floor; non-UTF-8 one-line failure;
`--from-raw` error labelling; `.json.tmp` sweep; shared `stemwell/state.py`
reader) — wave5's trailing-space proposal is moot, wave1 landed it. Three
slow/flaky tests never exercised by any wave validation. `BE→beta` lowercase
label, flagged independently by wave2b and wave3 and not on the quirk table,
so an unplanned quirk the seed introduced. wave2b's `logging.basicConfig`
observation. wave2a's `model_identity` reads `anthropic:claude-opus-5.5`
where every other record reads `claude-opus-5-5` — a formatting slip in the
string the surface showed or the worker typed; harmless now, a mismatch for
any epoch read later.

## Arc claims block

Summed validation of the subtree, stated as claims for reconciliation
against the arc oracle:

- Seven sessions applied; eight apply attempts; one HOLD, corrected by a
  retry that changed only the tests that pinned a moved byte.
- 57 claim/verdict rows across the arc: 54 agree, 1 `n/a` (seed
  `E3-dict-order`, precondition absent in the sandbox), 2 disagree (both
  wave2a HOLD rows, both on the Total line's trailing space).
- Every validation that ran passed in bale's staging; every validation
  declared its omissions in `validation_will_run`.
- Clarification rounds: 0 in every session. Light blocks: 0 from any
  worker. Probes: 1 (wave3).
- Budget pressure: `none` in every self-report; compaction: none; sandbox
  confined and no network grant in every attempt.
- No autonomy exercised: every open, paste, apply and answer was carried by
  the operator; no hook, oracle mechanism, cache or trust grant was
  introduced.
- First wave wall clock after the seed: 22 min 25 s (12:51:21 → 13:13:46
  UTC) for six sessions. Seed v2: 45 min 52 s.

## Consumed vs deferred scope

Consumed: every forecast in full except wave5's, which forecast five paths
and changed four — `commands/tally.py` was in the forecast and needed
nothing, because `iter_stem_lines` re-raises into the `OSError` handlers
tally already had. Four paths admitted beyond forecast, above.

Deferred: the five parked proposals (S6); `tests/test_fold.py`,
`test_sink.py`, `test_soak.py` never run by a wave (the seed ran them only
under its own `timeout 20`/`timeout 5` guards, and declared the unguarded
suite not run); the locale test, now closed rather than deferred — see
finding 2.

## Proposals

1. **Staleness flag at reconciliation.** Bale holds both timestamps; when a
   DISAGREE row's failing check touches a path landed since the session's
   `packed_at`, mark the row as read-side staleness rather than a bare
   disagree, and briefs name sibling surfaces in motion. Rationale:
   wave2a's HOLD was two DISAGREE rows on one byte that wave1 moved 14
   seconds before 2a's apply; the retry's `includes_missing` had to carry a
   *decision* ("is `context/report.py` current?") because no field existed
   for it.
2. **"Will create" forecast entry.** Admit a nonexistent path at pack time
   so new-file sessions stop paying a prompt per path. Rationale: 2a and 2b
   paid two prompts each for files the brief itself said could not be
   forecast. Weigh against ADR-0015's existence rule; the entry should
   still be a forecast, not a grant.
3. **Hot reads in every include set.** A file the runtime reads
   (`pyproject.toml`, the parser behind a command) ships with every pack
   that exercises the runtime, disjointness or not — PLANNER.md §6's second
   clause, applied to runtime reads rather than imports. Rationale: waves 1
   and 5 self-reported `pyproject.toml` missing and built stand-ins; wave3
   self-reported `commands/ingest.py` missing and probed for `tally.py`.
   The design desk's packing caused more probe pressure than the
   environment did.
4. **Plain-language brief framing.** A brief that reads as adversarial
   ("hostile", "planted", "must stay ignorant") is refused by the worker
   surface's safety classifier before any worker sees it; state what the
   fixture is and why the operator is blind. Rationale: seed v1 sat
   1 h 41 min from pack to abandon; v2, same design, reworded, landed in
   46 min.
5. **Probe timing, two numbers.** Round trip (post to paste-back) is
   chat-clock time and measures the operator's attention as much as the
   environment; run time belongs in the probe's own paste-back trailer,
   self-stamped. Today a probe leaves no telemetry row at all — wave3's
   exists only in `judgment_calls` and notes — so bale should record the
   post/paste-back pair as a session attempt, and the probe skeleton should
   stamp its own start and end. Rationale: the only source for wave3's 2
   minutes was the operator's memory.

## Findings by watch item

### 1. Hot-file forecast serialization — chafes, and the gate is right

Batch one opened four sessions in 17 seconds (12:51:21–12:51:38): wave1,
wave2a, wave3, wave5, all forecast-disjoint. wave2b's `bale open --check`
was refused at the disjointness gate against 2a's `pyproject.toml` forecast
(rehearsal, no open spent, no telemetry row). **Serialization gap, 2a open →
2b open: 15 min 40 s** (12:51:26 → 13:07:06); 2a landed at 13:02:20, so
4 min 46 s of that is operator latency after the gate cleared. wave4
serialized the same way on `report.py` behind wave1, which the brief did not
book: wave1 landed 12:58:46, wave4 opened 13:07:41, 8 min 55 s later. The
refusal names the collision and offers four remedies; only "apply the open
session first" is honest here.

The second cost, unnamed by the row: **read-side coupling.** Disjoint write
forecasts admitted wave1 and wave2a together; 2a's validation asserted
`report`'s Total line byte-for-byte from its packed `context/` copy; wave1
landed 14 seconds before 2a's apply and moved that byte. Result: HOLD, two
DISAGREE rows, checkpoint PASS, response correct. ADR-0015 has no word for
this; proposal 1 is the word.

### 2. Validation runtime budgets — chafes quietly

No wave validation ran `test_fold`, `test_sink` or `test_soak`. Every
session that touched the suite excluded by file with a declared `[SKIP]`:
wave1 and wave4 dropped the label-order test; wave2a ran
`test_meta`/`test_prune`/`test_ingest` only; wave2b skipped `test_ingest` by
design; wave3 ran `test_codec` alone; wave5 ran `test_ingest` and
`test_tally`. Self-reported runtimes: seed ~27–31 s; wave2b well under a
second; wave3 a couple of seconds; wave5 about a second; waves 1, 2a, 4
unstated. Telemetry carries no validation duration. The two-minute target
was never approached because workers route around it; the scheduled flake
never fired.

The locale question closes: **the operator's shell is C-type**, so
`test_report_lines_in_label_order` fails in staging too, and has never
passed on any machine the wave touched. wave4's worker guessed the other
way. Both exclusions were correct for staging, not just for the workers'
containers. `validation_will_run` carried every omission honestly, every
time. No proposal to the contract; the budget is met by omission, and the
report says so.

### 3. Ceremony floor — measurable now

wave1: **one character** of code change in `report.py` (plus the test edits
it needed). The response tarball carried six files — `manifest.json`,
`apply.sh`, `validation.sh`, `notes.md`, and the two mirrored sources — and
**[bytes: fill from `bale stats`, not in the pack]**. Session wall clock
7 min 25 s. wave2a/2b: **two admit prompts per new-file session**, four
total, for paths the brief named as unforecastable. Proposal 2.

### 4. Misunderstanding off doc work — did not dominate

wave5 was the designed trap: two parsers, five read sites, no docs. The
worker found all five sites by reading, changed two files, asked nothing,
probed nothing, and flagged the trailing-space checkpoint risk unprompted.
The wave's one HOLD was mechanical staleness, not intent. Zero
clarification rounds in seven sessions. On this corpus the row's premise did
not reproduce.

### 5. Probe economics — one round trip, split in two

wave3's probe was well-shaped and answered by running. **Round trip: 2
minutes** (operator's clock; chat-window time, attention included). Two
questions in it: one environmental (python version, `tomllib`), one
planner-caused (`tally.py` not in context; `ingest.py` also missing, worked
around with a stub and self-reported). Waves 1 and 5 built stand-ins for the
missing `pyproject.toml` and said so rather than probing. Finding: a file
the runtime reads is a hot read and belongs in every include set; the design
desk's packing caused more probe pressure than the environment did.
Proposals 3 and 5.

### Design-desk defects (their own line; not the environment's)

- Seed v1 refused by the worker surface's cyber safeguard on the brief's
  wording; 1 h 41 min from pack to abandon; v2 reworded, same design,
  landed. Proposal 4.
- The design desk's own `--write .` on the seed refused by the blindness
  gate at rehearsal — the self-oracle shape — which is why the initial
  commit carries placeholder directories.

## What S6 receives

Numbers: serialization gap 15 min 40 s (2a→2b), plus wave4's 8 min 55 s
behind wave1; ceremony floor six files per one character (bytes from
`bale stats`), two prompts per new file; probe round trip 2 min; validation
runtimes by session with omissions as above; zero misunderstanding on the
designed trap; locale test fails on C-type staging. The five proposals
above. The parked worker proposals, held until S6 by this sitting's
decision. No autonomy exercised.

## Sitting close — light-block ledger

Two light blocks emitted. Block 1 (three questions): [1] answered inline
(2 min), [2] answered inline (C-type), [3] returned as a question and
re-emitted. Block 2 (one question): answered inline (wait for S6). None sent
formal; none unanswered.
