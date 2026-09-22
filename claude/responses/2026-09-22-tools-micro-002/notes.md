# Notes — 2026-09-22-tools-micro-002

## Correction (this tarball corrects the held first attempt)

The blind checkpoint held the first attempt on one probe,
`lint-request-flag-silent-inside-forecast`: "an in-forecast path must
raise no forecast_departures line". I reproduced the problem against
this response itself. With every path in the forecast, the lint still
printed `[PASS] forecast-departures — with --request: every changes[]
path outside resolved_scope has a forecast_departures entry ...`,
because I had put the field name in the check's registry description,
and the runner prints that description on the check's `[PASS]` line.

My own tests and `validation.sh` missed it because they checked for
the warning code, or for a line naming the fixture's path. Neither
checked the whole output for the word. The probe's reading is the
right one: silence means the word never appears in the output.

The fix is in `tools/response_lint.py`:
- Neither request check's description names its subject word any more
  (`forecast_departures`, `README.md`).
- A warning can carry a short `headline`. The runner prints the
  warnings' headlines on the check's `[WARN]` line, and falls back to
  the description when a warning has none.
- So the words appear only when a check warns: on the `[WARN]` line,
  e.g. `src/new.txt has no forecast_departures entry`, and in the
  `~` detail line beneath it.

The README check had the same shape, a `[PASS]` line naming
README.md. Its probe passed, but I fixed it the same way rather than
leave the asymmetry.

The regression coverage is in `tests/test_response_lint.py` and
`validation.sh`:
- Whole-output silence is now pinned in the suite for in-forecast
  paths and for a read or absent brief.
- `validation.sh`'s forecast check is renamed "...; silent when all
  inside" and asserts the same.
- The new assertions fail against the held tarball's tree and pass
  against this one.

Only `tools/response_lint.py` and `tests/test_response_lint.py`
changed from the held attempt; the other three files are
byte-identical to it.

One correction to the judgment calls below. The item 3 paragraph says
warn lines append the check's description. They now carry the
warnings' headlines instead, and fall back to the description only for
a warning without one (the two pre-existing warning checks).

All five items and rider A landed. The response is bumpless: nothing
touches `bin/`, `schemas/`, `BALE.md` or `claude/changelog/`. There
are no out-of-forecast paths. All five `changes[]` paths are the named
forecast, which is why the crafter omitted `forecast_departures` when
I crafted this manifest with `--request` against the real request.

## Judgment calls

**Item 1: emit exit.** `--emit-feedback-mechanical` now exits 0
whenever it wrote the object, with or without findings. When findings
exist, stderr says "emitted despite N finding(s)" and points at the
plain re-run as the verdict. The open half was mine to decide: when no
object can be emitted (manifest.json unavailable), it still exits 1,
so an `emit && paste` chain stops when there is nothing to paste.

Three existing emission tests pinned exit 1 on a degraded directory.
They now expect 0, with the degraded values as the evidence. This
response is a live specimen: the landed emitter exited 0 on its own
seeded block, whose four placeholders were the only findings. After
the paste, the plain lint ran clean.

**Item 2: `--request`, warning tier.** `FORECAST_DEPARTURE_UNDECLARED`
is a warning, for the reason the brief gave: the path may be
legitimate drift that the operator admits at apply, and bale's
own-forecast gate is the enforcement. The check names the
`changes[]` path and says `forecast_departures` in the same message.
Directory entries cover their subtrees, matched on whole path
components, so `tools` does not cover `toolsmith.py`. A trailing
slash and `.` are both tolerated.

Without the flag, or when the request predates `resolved_scope`, the
check reports `[SKIP]` with the reason. I added a small
`CheckSkipped` exception to the runner for this, because a vacuous
`[PASS]` would have been a silent skip. An unreadable or non-object
`--request` file exits 2, which is bad usage and matches `--schema-dir`.
An unfilled crafter stub (`why: ""`) is left to the schema, which
reports it as `SCHEMA_VIOLATION`; this check never reports it twice.

**Item 3: README.** The warning is `README_NOT_IN_DOCS_READ`. It fires
when `docs_read` is absent as well as when it omits the brief. That
matches the motivating specimen, which never opened the brief. A
`docs_read` entry "names README.md" if the file name appears anywhere
in it, so `README.md (the brief)` counts.

For the output to be a `[WARN]` line *naming* README.md, I changed
how warn lines render: they now append the check's description,
e.g. `[WARN] readme-in-docs-read — 1 warning(s): with --request: a
shipped brief (readme non-null) is named README.md in docs_read ...`.
This is additive; no test or `bin/` code parses that text.

**Item 4: crafter seeding.** This is a flagged deviation, so look
here on review. The brief says "every `files/` path"; I seed every
`changes[]` path, which adds deleted paths. The schema's own wording
is "one entry per changes[] path the worker shipped outside the
session's write forecast", and apply's drift gate treats a deletion
like any other path. Say if you want deletions left out.

Other seeding behavior:
- Stubs follow `changes[]` order.
- With no departures, the key is absent.
- A request without `resolved_scope` gets a log line instead of stubs.
- A malformed `resolved_scope` exits 2.
- Bailout and clarification responses seed nothing, because their
  `changes[]` is empty.

The forecast predicate is written once in each tool, since neither
imports the other. A shared-case parity test in the crafter suite
pins the two copies together.

**The §5.4 wording.** The new sentence reads: "Given `--request`,
`tools/craft_response.py` seeds one such object per `changes[]` path
outside the request's `resolved_scope`, its `why` left empty — an
unfilled stub cannot pass the lint — so the `why` is the worker's to
fill; a session with no such path omits it." It cites only `tools/`,
and `test_global_doc_selfcontainment` stays green.

**Rider A.** VERBATIM-1 is appended to the same paragraph as the
anchor sentence and wrapped at the file's width. `validation.sh`
checks it inside §7.5, directly after the anchor, exactly once,
comparing whitespace-normalized words. §5.9 is hash-pinned
byte-identical to the base.

**Findings §8 item 4: the epilogue.** I read the emission and chose to
change stderr only. The combined stdout is pinned byte-equal to the
three joined fragments (`CraftEpilogueFragments`), so a louder banner
in the stream would break a contract that callers of the flagless form
rely on. A refusal without `--fragment` would break every worker's
existing habit for a hazard that is diagnostic, not destructive: an
early `reconcile_claims` just prints `[n/a]` rows.

The log line now opens with "COMBINED emission". It explains that a
one-block paste fires the call before any verdicts are recorded, and
names `--fragment definitions|assertions|call` before the
cut-at-the-banners instructions. If sonnet5-b-style pastes keep
happening, the next step up is making `--fragment` the documented
default in §7.3's prose.

## Worth a close look

- `validation.sh` was run twice, as §7.2 asks. On the changed tree
  every check passes. On the unmodified tree, every session assertion
  fails except two guards, which pass there by design: the §5.9
  preservation hash and the exec-bit checks.
- I also ran the full suite tree in the dotted form. 71 of 72 are
  green. `test_changelog_record` fails because `claude/changelog/`
  isn't in the request, and it fails identically on the base tree.
  `test_handoff_fixture` is a helper module with no tests.

## Proposals

**What:** Drop the other two redundant `tests/`-on-path guards, in
`test_doc_crossrefs.py` and `test_sanctioned_pairs.py`.
**Why:** This is board 113's proposal. The craft guard went this
session and its class stayed green in the dotted form; the other two
were outside this forecast.
**Scope hints:** Those two files only.

**What:** Have the lint's `forecast-departures` check also warn on a
declared departure that isn't one: an entry whose `path` is inside
`resolved_scope`, or that names no `changes[]` path.
**Why:** `bale stats` cross-checks declarations against admitted
paths, so a stale entry (the file was moved back in-forecast, or the
path was renamed) would read as a false departure. The lint now has
the forecast in hand to catch it.
**Scope hints:** `tools/response_lint.py` and its suite. Warning tier,
like the rest of the check.

**What:** Mention in TARBALL.md §5.2.2's fill workflow that the
emitter exits 0 once it writes, and that `--request` enables two
warnings.
**Why:** The workflow paragraph is where a worker learns to chain
emit and paste, and it still reads as if the emitter's exit is the
verdict. I kept this session's doc edits to the two sentences the
brief pinned.
**Scope hints:** `docs/TARBALL.md` §5.2.2, a sentence or two. It
could ride with the §5.9 holder, or with any later TARBALL.md touch.
