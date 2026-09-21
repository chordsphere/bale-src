# Notes — 2026-09-21-board-103-doc-lane-006

All seven deltas and the rider landed, in the three forecast files and
nowhere else. Bumpless: no `bin/VERSION` entry, no changelog record. No
heading, step or item moved. Both VERBATIM sentences landed as written; I
checked each against the code before placing it and neither is wrong on
the facts, so there is no correction to rule on.

## The rider: the clause, not nothing

Row 37's open entry closes with **the clause**. `docs/CLAUDE.md` §11.4
already had a sentence ending at `TARBALL.md` §5.6.1 ("The bailout
response's empty change surfaces are specified in..."); it now continues
"which also mechanizes the whole artifact set: the crafter emits it, so a
bailing worker fills judgment, never shape."

Why a clause rather than nothing: §11.4 is read at the one moment budget
is the problem, and the fact that the bailout set is tool-emitted is what
makes a late bail affordable. It changes the "will the remaining work
fit" arithmetic §11.3 asks for, and it is the one thing about the shape
worth knowing before the drill-down rather than after. Why only a clause,
and why it names no flag: §5.6.1 stays the single home of
`--kind bailout --write`, so the spelling cannot drift in two places.
That is the bracket's "at most a clause", taken literally.

## Where I used the latitude

Places to look at review, most consequential first.

- **Delta 6 has two homes, not one.** The proposal names §10.3 step 3
  only. But §10 opens "where a step compresses a section, the cited
  section wins", and §5.9.2's lead calls `notes.md` "the prose channel"
  with no courier caveat, so a checklist-only fix would have left the
  checklist carrying a rule its own section contradicts by omission. I
  stated the rule in §5.9.2's lead and let step 3 compress it with a
  pointer. If you want it checklist-only, §5.9.2's added sentence is the
  one to strike.
- **Delta 5: marked, and inlined.** The paragraph now calls the §15 read
  planner-side and then gives the asker the two sentences it would
  otherwise go looking for: a `batched` question leaves the worker
  proceeding on its `default_assumption`, a `blocking` one suspends the
  session. I inlined because the old text said the doctrine covers "what
  the two priority classes mean for the asker", and the asker is the
  worker; telling a worker not to follow a pointer that advertises
  something for it needs the something. This is a deliberate, small
  duplication of §15's priority bullet. If §15 moves, this paragraph
  follows.
- **Delta 3, §7.1: one sentence beyond the ask.** You flagged as
  unverified what bale does about an unannounced validation-time write. I
  checked `bin/bale_staging.py` at 0.4.40: reconciliation runs before
  `validation.sh`, nothing walks the tree after it, and the commit is
  built per `changes[]` entry, so a stray `__pycache__/` is neither
  caught nor committed. §7.1 now says nothing mechanical catches it and
  "the printed list is the whole of the check". I worded that from §7.1's
  own step order (step 4 precedes step 5) rather than from the
  implementation, so it holds as long as the documented pipeline does.
- **Delta 7: conditional on being able to run.** §5.3 says "Claude
  doesn't run validators", with `claim_basis: observed` as the documented
  exception, so the sentence opens "A worker that can run its script
  before shipping runs it twice". It sits in §7.2 after the checklist,
  not in §7's lead, so the relay paragraph and the extractor self-test's
  marker words are not in play at all.
- **VERBATIM-1 and "never the bytes".** It is its own paragraph between
  the worker-side flow and the parity paragraph, so the parity paragraph
  ("the integrity trailer is a hash of the body") reads as its reason. I
  left the parity paragraph's closing sentence alone. I read the two as
  compatible, as you do: that sentence is about the block's layout being
  held by parity tests rather than prose, and the escaping rule is a
  transport fact about a block the worker did not lay out.
- **Delta 2 spelling.** My first draft wrote the field as one dotted
  code span, `feedback.self_reported.forecast_departures`, which does not
  contain the required spelling with its backticks. My own new pin caught
  it. Both homes now read `` `forecast_departures` `` with the stream
  named separately.
- **Delta 4** sits in the "Documentation is the work" row's Situation
  cell, since it narrows the trigger. The "| Every session |" row is
  untouched.

## The pins I added

`tests/test_doc_crossrefs.py` gains `ByteDisciplinePins` (5 tests; the
three doc suites go 36 to 41). VERBATIM-1 is pinned in §5.9.2 alone,
VERBATIM-2 in §7.2's item 6 alone, and that test also requires the list
to still be items 1 to 6. `forecast_departures` is pinned in §5.4 (before
§5.4.1) and §10.1, with its keys read from
`schemas/response-manifest.schema.json`'s `required` list rather than
hard-coded, the way the relay pin reads its sentinels from
`bin/bale_report.py`. There is a bite test and an extractor self-test. I
did not pin the other deltas: they are authored wording around a required
spelling, and PLANNER.md §4 says authored text gets no connective-phrase
pin.

## What I ran, and what I did not

`validation.sh` does what the new §7.1 and §7.2 text asks: it suppresses
the interpreter cache and then asserts none was written, and every pinned
outcome is compared on bytes read in Python, never through `$(...)`.

I ran it twice, per Delta 7, against copies of the shipped `context/`
tree. With the change applied: everything passes. On the unmodified
tree: the two change-detecting checks fail (verbatim sentences, required
spellings; eleven spellings named missing) and the invariant guards pass
(numbering, no model or run name, no cache written), which is what a
guard should do on both. The doc suites pass on the unmodified tree too,
because there the suite is the base suite; the new pins run against the
base docs fail 10 ways, which I checked separately.

Every claim is `observed`. The bumpless and lane checks read
`.bale-manifest.json`, which only exists in bale's staging, so without
it they print `[SKIP]` with that reason. To exercise them I placed this
response's manifest at that path in my copy, the way §7.3 says bale
does: both pass, and all eight claims reconcile `[agree]`. As a negative
control I then doctored that copy with a `bin/VERSION` entry and a
`docs/PLANNER.md` entry, and both checks failed. What I have not
observed is bale's own staging, sandbox included; your apply is the
first run of that, as it is of the checkpoint.

I did not run the full test suite, only the three doc suites, the same
as your desk. Nothing outside those three reads the passages I touched,
by your pin search; I did not repeat that search beyond confirming no
suite pins the `--doc-assertions` code span I briefly had wrapped across
two lines (I put it back on one line regardless).

## Proposals

- **What:** seed `forecast_departures` from the crafter when `--request`
  is given. It already reads the request manifest, which carries
  `resolved_scope`; any `files/` path outside that forecast could be
  emitted as a `{path, why: ""}` stub, invalid until filled, like the
  other sentinels.
  **Why:** Delta 2 tells workers the field exists; this would make it
  appear on its own exactly when it applies. The docs now say "the
  crafter does not seed the field", which is true at 0.4.40 and would
  need the matching one-line edit in §5.4.
  **Scope hints:** `tools/craft_response.py`, its suite, §5.4's new
  sentence. A tool change, so out of this session's scope by the brief.
- **What:** decide whether an unannounced validation-time write should
  stay review-only. A post-validation tree walk against the
  pre-validation snapshot would turn §7.1's "no surprise writes" into a
  contract rule.
  **Why:** I found at 0.4.40 that nothing checks it, and §7.1 now says so
  out loud. That is honest, but it is also an invitation to decide
  whether the gap is wanted.
  **Scope hints:** `bin/bale_staging.py` (`run_validation_sh`);
  `.validation-logs/` and `.bale-manifest.json` would need exempting.
- **What:** §5.9.2's first paragraph and the exchange-record paragraph
  could say once, plainly, which artifacts each courier carries. Today
  that is assembled from three places.
  **Why:** writing Delta 6 meant reconstructing it. Small; fits the next
  §5.9 holder.
