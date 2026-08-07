# notes.md — 2026-08-07-ratification-microdeltas-014

## The §1 verification

The shipped `bin/bale`'s VERSION constant reads `0.4.3` (line 225),
matching the value the §7 sentence records, so the marked-relay
clause was trued up to verified-at-sid naming this session per the
brief. No disagreement to report on this item. Two mechanics notes:

- `validation.sh`'s version assertion runs against the **staging
  tree's** `bin/bale`, not the request's shipped copy — the shipped
  copy isn't reachable at apply time. I verified the shipped copy
  here; the assertion re-establishes the same agreement against the
  repo the sentence will actually describe. If the two ever
  diverged, that divergence is exactly what the check should catch.
- The trail parenthetical's bump-exempt enumeration was **not**
  extended with 013 (tests-only) or the two doc-only deltas
  vehicles (012, this one). The brief's §1 asked for the relay
  clause only, and the parenthetical as landed enumerates the
  sessions inside the 0.4.0 → 0.4.3 span; appending every
  subsequent bump-exempt session would accrete without bound,
  against the header convention, and the exemptions are already on
  record in the board row and the §5 cadence rulings. Confirm this
  reading; extending the list is a one-line follow-on if the desk
  prefers it.

## Where shipped text met the brief's assumptions

Everything the brief named was found where it said: the header line
at its v4 position, the board-35 row with sessions 1–3 and the
stale queue paragraph, the 009/010/011 judgment block as the last
one, the `build_request_tarball` registry entry, and the §7
sentence carrying 012's marked-relay clause. The 013 notes' numbers
agree with the brief's row text (323 tests, ~111s scaled). No
disagreements.

## Judgment calls

- **The Remaining-queue paragraph is edited in place, not
  appended past.** The brief's item 3 says "append per the arc's
  entry style" and then states the new queue picture; the Session 4
  entry is the append, and the queue paragraph is the row's
  current-picture line — record-then-current, per the 012-ratified
  call, puts the dated DONE entries in history and edits the
  current line. The old "gap 3 (in flight)" wording is gone; the
  absence is asserted in validation.
- **Absence anchors are normalized, not single-line.** The two
  replaced passages (§7's relay clause, §4's old queue line) wrap
  mid-phrase in the shipped file, so a single-line fixed-string
  absence grep is blind to them — caught by a negative validation
  run against the unedited file during build. Presence anchors stay
  single-line fixed strings per DOCS.md §9; the two absence checks
  join wrapped lines first, per the same section's normalization
  note.
- **Verbatim quotes** (013's two proposals, What/Why) were copied
  from the archived notes file shipped in `context/`, not from the
  brief's restatement, and fingerprint-verified normalized against
  it. The second rider carries the proposal's title in quotes; the
  --slow entry's re-trigger, harness-level scope, and current
  margin are recorded outside the quoted What/Why, as the brief
  specified them.

## Proposals

### True up §3's stale pack-guards in-flight sentence

**What:** §3 "In flight" still says "The gap-3 pack-guards session
is in flight, concurrent with this one." — false once Session 4 is
DONE, and "this one" refers to 012's landing vehicle besides. A
one-line edit (drop the sentence, or fold "the board-10 spec-intake
sitting moves to the head" into a trued-up bullet).

**Why:** Not among the brief's enumerated deltas, so per the
sitting-close flag-don't-fix precedent (and its ratified line this
session records) I left it and flagged it. It sits in a
current-picture section, so unlike Session 1's dated record it will
read as wrong, not as history, to the next reader.

**Scope hints:** `claude/MASTER.md` §3, first bullet block; rides
any next MASTER.md touch, or the sitting-open pass.
