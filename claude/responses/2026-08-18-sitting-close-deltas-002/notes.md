# notes.md — 2026-08-18-sitting-close-deltas-002

## The base pin (chat-resolved clarification, recorded per TARBALL.md §4.5/§5.9.1)

The brief's base-identity checks split: the header sid matched
(`2026-08-18-master-v5-regeneration-001`), but the shipped copy is
**2575 lines**, not the recorded 2574 — a genuine count, verified at
the byte level (single trailing newline, no double-blank at EOF). Per
the brief's "either check failing → kick back" and with
`expects_probe: no` in force, I asked in chat rather than proceeding
or probing.

**Question asked:** is the shipped copy the true applied-v5 base
(recorded figure off by one), or did the base move post-v5?

**Answer (architect, at the desk, against the live tree):** reading 1
confirmed — live tree is 2575 lines, sha
`e770806d375037e5337480818dd8b16fd74d16275339d597be63653415a01c1f`,
last touched by the v5 landing commit (209ffa0). The 2574 figure was
desk-attributed: transported from v5 notes accounting written against
the held branch before the retry's longer landmark sentence re-wrapped
one extra line. Not drift. Proceed on architect authority with 2575
plus that sha as the corrected base pin.

**The pins, stated for the desk (the brief's requirement):**

- Shipped base copy (= confirmed live tree):
  `e770806d375037e5337480818dd8b16fd74d16275339d597be63653415a01c1f`,
  2575 lines.
- Landed copy this response ships:
  `c1f190ad1bbfdde229db266441dfca8b051c24ce39b8e948787af14c7528174b`,
  2655 lines (80 net new).

Boards 40/41/48 remain the standing close for this class; this
session is another specimen for them — the count-vs-sha proxy split
exactly the way an in-brief sha pin wouldn't have.

## Verification performed (session side)

- Landed-vs-brief equality of Blocks A, C, D, E, F and Block B's new
  clause: whitespace-normalized whole-block containment, block texts
  extracted mechanically from the brief (never retyped) — the same
  extraction the landing itself used. All equal.
- Block B's old clause absent (normalized).
- Diff shape reconciled with a sequence-matcher pass: **zero pure
  deletions, exactly two replaced regions** — the header line and the
  §5 clause lines — everything else pure insertion.
- Wrap convention held: the landed file introduces **no new over-72
  lines**; the base's eleven long lines ride through unchanged.
- `validation.sh` re-runs the landed-state half of this in staging
  (equality, old-clause absence, header, line count) and was
  negative-tested against the unedited base (all four checks FAIL
  there — the oracle discriminates).

## Placement and formatting calls to ratify (all latitude, none silent)

- **Block B landed as a minimal two-line replacement.** The old clause
  starts at a line boundary in the file, so the paragraph's first four
  lines are byte-identical; only the clause's two lines were replaced
  by the new clause's three (re-wrapped, `):` suffix carried). This is
  the tightest reading of "nothing else in §5 changes."
- **Block D precedes rows 47/48**: the bracket appends at the end of
  row 46's body (its 4-space continuation indent), then a blank line,
  then rows 47 and 48 — so the bracket stays inside the row it
  annotates, per "appended at the end of row 46."
- **Block E** sits as an own-line bracket at the bullet's 6-space
  continuation indent, directly after "README, item 2.)" — the sibling
  bullet's `[2026-08-16: lifted to §5.]` is the in-file precedent
  followed.
- **Block A** lands after the 006 ratified-judgment-calls list,
  separated by one blank line, before `## 4` — the close-005 §3-end
  accretion convention.
- **Block F** lands as the fold-in registry's last bullet, before the
  "Landed 2026-08-05, non-board" dated paragraph that ends the
  registry proper.
- Re-wrap at the file's ~70-column convention throughout; long tokens
  (sids) never broken.

No out-of-forecast paths: the change set is exactly the declared
forecast, `claude/MASTER.md`. Nothing deferred; nothing to propose.
