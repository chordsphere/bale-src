# notes.md — 2026-09-15-board-101-bare-apply-cap-007 (re-attempt)

`corrects` names the first attempt, held at commit 7c4f244 with the
blind checkpoint 7/7 PASS and the worker validation exiting 1 on its
own step 5: my `validation.sh` grepped `validate.sh`'s output for
`result: PASSED`, and the script never prints that — its pass line is
`result: OK — N checks passed` (your run: 89/89). The sandbox never
showed me the OK wording because `README.md` is not shipped in the
request, so the `FAILED — 88 passed, 1 failed` branch was the only
one I ever exercised. The needle is fixed and both branches are now
rehearsed (a README-less copy and one with `README.md` present). The
change set is byte-identical to the first attempt: `files/`,
`apply.sh`, and every `changes[]` hash are unchanged; `validation.sh`
step 5 and this preamble are the whole diff.

One-apply-behind, as the brief says: the apply that lands this runs
the 0.4.31 resolver one last time, so it opens every `*.tar.gz` in
your Downloads once more. From the next apply on, it opens two.

`bin/VERSION` → 0.4.32.

## Out-of-forecast drift — admit at apply

- **`bin/bale_report.py`** — the `caller == "handoff"` branch of
  `format_checkpoint_scope_refusal` (the narrowing-remedy pick) and
  the docstring paragraph describing it. The brief says "read the
  gate in `bin/bale` before editing; if the same message serves both
  cases, split the remedies by which rule fired." The gate call is in
  `bin/bale`, the gate is in `bale_pack.py`, and the message — the
  thing the ruling is about — is rendered here. As shipped, the
  handoff branch was chosen *before* `side` was consulted, so a
  handoff's read-side refusal offered the forecast-side `--write`
  lever; the desk's ruling cannot be met without this file. One
  branch, the same one row 73b touched as flagged drift and you
  ratified. Nothing else in the file changed.

`feedback.self_reported.forecast_departures` carries the same path.

## The three rules, as landed (`resolve_bare_apply_tarball`)

1. **Name is the pre-filter.** The scan globs `response-*.tar.gz` and
   nothing else. A file not so named is not stat'ed, not counted, not
   mentioned — it is outside the surface, the way a `.zip` always was.
   I chose *not* to count un-named tarballs in the refusal ("N other
   .tar.gz files ignored"): rule 1 says they are never read, and
   listing them would re-introduce a `*.tar.gz` glob for no decision
   the operator can make from it.
2. **Order by mtime, examine the two newest.** `BARE_APPLY_EXAMINE_CAP
   = 2`, a module constant beside the resolver, no config key. "Plus
   any file sharing the second's exact mtime" folds into one cutoff:
   every named file whose `st_mtime_ns` is at least the second-newest's
   is examined. That makes a tie at either rank visible in full, so
   board 87's tie refusal is byte-identical and the tie-at-the-second-
   rank case (newest is stale, next two tie) refuses too — pinned.
   Resolution runs among the examined candidates only, with the
   existing newest-wins code untouched: newest examined wins if it
   answers an open session, else the second, else refuse. An older
   candidate is never opened and never found — pinned by asserting its
   path is absent from the refusal.
3. **The refusal names what it examined.** The no-candidate refusal
   now reads: the open-set line as before; `searched (response-*.tar.gz,
   non-recursive; only the two newest by modification time are
   examined):` with the directories; `examined and rejected:` with one
   line per examined file — `<path>  — answers <sid>, which is not an
   open session` or `<path>  — not a candidate: <peek reason>`; then,
   only when it applies, `N older response-*.tar.gz file(s) not
   examined: bare apply opens only the two newest.`; then the existing
   remedy sentence. With no named file at all it says `examined:
   nothing — no response-*.tar.gz file in these directories.` The
   `--verbose` per-file skip lines survive for the examined files, and
   `--verbose` adds one line up front: `N response-*.tar.gz file(s)
   found; examined the M newest by modification time (K older not
   opened)`. The resolved-path log line when a skip occurred now says
   `examined tarball(s) not candidates`. The old aggregate line
   ("N tarball(s) were scanned and are not candidates") does not
   survive — `validation.sh` greps for it.

Everything after resolution — echo, y/N, non-TTY decline, pipeline —
is unchanged. `_peek_bare_candidate` is unchanged in code; its
docstring now says why the caller bounds how many files reach it
(`getmembers()` decompresses the whole stream).

## The row-89 decline remedy — my call: yes, beneath the line

The three `BARE_APPLY_DECLINE_LINES` are byte-exact (the parity suite
pins them literal and single-line, and the pty pins assert `bale apply
<path>.`). When the other examined file also answered an open session,
the decline appends, after the table line:

    The other examined file also answers an open session:
      bale apply /path/to/response-<sid>.tar.gz  (answers <sid>)

One command per physical line (TARBALL.md §1), the path through
`shlex.quote` — the non-TTY refusal's `bale apply {path}` is unquoted
and I left it alone, but a Windows Downloads name with `(1)` in it
would break an unquoted paste, and the alternative exists to be
pasted. It is a plain list, so the tie-at-second-rank shape (two
alternatives) renders both. Pinned under the pty; the single-delivery
declines assert the block is absent. Worth the eight lines, I think:
the placeholder remedy told you to type a path you were about to look
up; this one is the path.

## `bin/bale` — the two strings

- The `apply` subparser description's bare-form paragraph now says:
  lists the `response-*.tar.gz` files, opens only the two newest by
  modification time, resolves the newest of those answering any open
  session, the no-candidate refusal names each examined file, and
  files not named `response-*.tar.gz` are never candidates and never
  opened. `widened v0.4.29; bounded v0.4.32` in the parenthetical.
- The positional's `help=`: "answering the open session" → "answering
  an open session". Two words, as proposed.
- Left as riders say: run_hook's f-string cleanup, the wizard picker.

## The handoff blindness gate — both dispositions

Both cases in `HandoffBlindnessGateTest` fail on the shipped tree
exactly as the desk read them; both are rewritten, neither skipped or
deleted.

- **`test_handoff_refuses_covering_reading_plan`** now asserts the
  read-includes phrase (`READ_NAME_PHRASE`, which the suite already
  defined for the pack side) and asserts the forecast-side phrase is
  *absent*; asserts the new read-side remedy (`re-bail with a reading
  plan that does not name the checkpoint (a handoff's read set is the
  bailout's reading plan, which `bale handoff` ships as includes;
  --write moves the forecast, not the reads, so it is not the lever
  here)`) and that neither the `--write` remedy nor pack's `drop the
  --include entry` appears; the flag-successor and pre-sid assertions
  are unchanged. Two things to ratify in the wording: (a) the diagnosis
  still opens `pack includes name the blind checkpoint explicitly …`
  on a *handoff* — the ratified constraint is that diagnosis text stays
  byte-shared across callers, so I did not touch it; (b) "re-bail" is
  the honest verb — a handoff's read set is the bailout's reading plan
  and no flag on `bale handoff` reshapes it, so the only read-side fix
  is a bailout whose plan does not name the oracle, or the flag. The
  `OLD_PLAN_REMEDY` string that `test_handoff_checkpoint_gates.py`
  asserts absent on the *forecast* side ("…does not cite…") is not
  reused; the new sentence says "name", which is the gate's own key.
- **`test_handoff_empty_plan_whole_tree_refuses`** →
  `test_handoff_empty_plan_inherits_the_parent_forecast`: the same
  fixture (parent packed `--include hello.txt`, no `--write`, so the
  recorded forecast is `["hello.txt"]`; empty plan) now asserts exit 0,
  `checkpoint blindness gate passed`, neither refusal phrase, the new
  session's `scope.json` equal to `["hello.txt"]`, and provenance
  `checkpoint_scope_admitted: false` beside the checkpoint stamp.
  The `[\".\"]` fallback lives behind `drop_parent_record` in the gates
  suite, as row 73b left it — not duplicated here.

The gate message change itself: only the handoff remedy sentence
splits; pack's two remedies and the forecast-side handoff remedy are
byte-identical (`test_handoff_checkpoint_gates.py`'s
`WRITE_NARROWING_REMEDY` pin still passes — it ran in the touched
suites).

## Tests

`BareApplyResolutionTest` is 24 cases (from 17). Every fixture
response is delivered as `response-<name>.tar.gz` now; `raw_name=True`
drops the prefix for the pins that prove an un-named file is never
opened. The proof for "never opened" is behavioral rather than a
monkeypatch: the un-named `junk.tar.gz` and `request-…tar.gz` carry
*valid response content answering the open session* and are newer
than the real delivery — if either were opened it would be a
candidate and, newest, would win and be echoed. A third un-named file
is unreadable (mode 0) — if opened, `--verbose` would print a skip
line naming it. None of the three names appears in the output, and
the `--verbose` count says one named file was found. (The mode-0 leg
is inert under root; the content leg is the one that carries.)

New pins: the pre-filter, the cap naming both examined and counting
the unopened one, second-newest wins, tie at the second rank, the
`--verbose` lines, the decline's named alternative, and the empty-
surface refusal. The old `3 tarball(s) were scanned` assertion moved
to the named form.

## Claims

- `session assertions` — **observed**.
- `unittest: touched suites` — **observed**: 43 + 16 + 31 + 11.
- `unittest: full discovery (--slow)` — **observed**: 1013 tests,
  green with `BALE_TEST_SLOW=1` in a staging-shaped copy of the
  shipped tree (`files/` overlaid, `apply.sh` run, manifest placed);
  ~195 s. One skip, pre-existing (a sandbox capability probe).
- `validate.sh (install sanity)` — **observed**: 88/89, the one
  failure `README.md present` (not shipped), as at rows 78 and 87;
  `validation.sh` passes the check on exactly that one failure and
  fails on any other.

## Surprises

- The module docstring of `bin/bale_apply.py` still says the module
  never imports `bale_pack`; there is a lazy `import bale_pack` at
  ~line 1144 in the shipped file. Pre-existing, not mine — I had
  written a `validation.sh` assertion on the docstring's claim and
  removed it when it tripped on the base tree. Proposed below.
- `unittest discover` takes one `-p`; `validation.sh` runs the four
  touched suites by direct execution instead.
- `BALE.md` §8's ruling sentence wraps across three lines; the
  byte-exact check in `validation.sh` includes the line breaks.

## Proposals

- **What:** either drop the "this module never imports `bale_pack`"
  sentence from `bin/bale_apply.py`'s module docstring or lift the one
  lazy import it contradicts. **Why:** a reader who trusts the
  docstring's dependency-direction claim (and a validation that greps
  for it, as mine briefly did) is wrong today. **Scope hints:**
  `bin/bale_apply.py` ~line 1144 and the module docstring; trivial.
- **What:** quote the non-TTY refusal's `bale apply {path}` through
  `shlex.quote`, matching the decline's alternative line. **Why:** the
  operator's search path is a Windows Downloads folder; a browser's
  `response-x (1).tar.gz` renders an unpasteable line. **Scope hints:**
  one expression in `resolve_bare_apply_tarball`; a pin in the piped
  decline test.
- **What:** the read-side diagnosis says "pack includes" on a handoff.
  **Why:** the byte-shared-diagnosis constraint keeps it that way; if
  the desk ever relaxes that, "request includes" reads right for both
  callers. **Scope hints:** `bale_report.py`, both suites' phrase
  constants; only with the constraint re-ratified.
