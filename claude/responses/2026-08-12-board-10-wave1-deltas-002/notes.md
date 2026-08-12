# notes.md — 2026-08-12-board-10-wave1-deltas-002

## The chat-resolved clarification (recorded per TARBALL.md §5.9.1)

**Question.** Edit item 2 named a "§3 position: Version line …
Latest-applied line …" — but §3 has no version line and no
latest-applied line anywhere in the shipped file; the version's one
home is §7's landmark per the 012 collapse, recorded twice in the
doc. Applying item 2 literally would mint a second version home.

**Answer (ratified in chat).** Item 2 is a contract on outcomes, not
mechanisms; the mechanism it named was wrong against the shipped
file. Ratified mapping: §7 trail advances to 0.4.4 at the S1 sid,
recorded as a claim (no bin/bale shipped to verify against), with S3
on the bump-exempt list and the 0.4.5-pending note; §3's position
bullets edited in place to the new position with the two wave-1 sids
and the orchestration.md line; header's "Last landed by" per the
header's own mandate. The §7 touch is sanctioned — the forecast
covers the whole file. Evidence numbering verified from the file
(max was 61), not the brief, per its own caution.

## Judgment calls to ratify

- **§3 bullet replacement scope.** "Edited in place to the new
  position" meant replacing both stale leading bullets — the closed
  tidy-up-sitting bullet (its record lives in §6 entry 57, the
  board rows, and telemetry) and the stale "Next, in order" bullet
  (the spec-intake sitting it forecast has now happened; ADR-0016's
  flip landed at the 08-07 sitting per the board 10 row's bracket).
  The remaining sequence is stated once, on the board 10 row; §3
  points at it rather than restating.
- **No version value in §3.** I first drafted "(0.4.4 live, 0.4.5
  pending at S2)" into §3's bullet and then removed it: §2's
  "Current version" pointer deliberately omits the number, and a
  §3 restatement would re-create the soft two-home the collapse
  forbids. §3 now carries only the pointer ("the version position
  is §7's, its one home"). If you want the number visible in §3,
  say so and I'll accept the duplication knowingly.
- **Board 10 row wording.** Status went into the bold header
  ("spec-intake DONE, wave 1 landed", matching the sibling
  phase-status style of rows 7/13); the original row description is
  retained after the annotation, introduced by one new word,
  "Charter:", to make the joint read. The bold-header instance of
  the phrase is line-broken before "wave 1 landed" so the phrase
  never wraps; the quoted anchor instance sits in the annotation on
  a single line.
- **§7 verification sentence reworked.** The old sentence claimed
  the whole trail "verified from the VERSION constant … with 014";
  that verification does not cover 0.4.4. I scoped it: "0.4.3 and
  earlier verified …; 0.4.4 a claim per the wave-1 brief — no
  bin/bale shipped with this session to verify against." The
  standing rule (verify with `bale --version` at each sitting's
  open) will true it up.
- **Placement/heading inventions**, all convention-matching but not
  brief-specified: the §6 divider "New from the board-10 wave-1
  sittings (2026-08-10/11):"; the board-10 agenda block heading
  "Added at the wave-1 landing (2026-08-12), for S6:"; the watch's
  "Re-trigger:" phrasing folding the brief's "record from the next
  apply paste and clear the watch" into the list's row shape.
- **Fold-in entry A's source line** cites "evidence 62's proposed
  counter" — the brief said the counter is "proposed in the fold-in
  registry", so the two entries cross-point; each carries its own
  content, no restatement.

## Out-of-forecast paths

None. The forecast is `claude/MASTER.md`, the one path shipped. The
blind checkpoint at `claude/checkpoints/current.sh` was not read,
shipped, or modified, per the cautions.

## Observed pre-existing drift (not touched)

The §3 Watches preamble enumerates its sources as 4 + 3 + 1 + 2 =
10 watches, but the list already carried 13 before this session
(now 14 with the WSL2-runtime watch). The enumeration went stale
before this session — at least the sweep-stamp, plan-less-handoff,
read-staleness, and forecast-precision additions postdate it — so a
partial fix appending "and one from wave 1" would repair my
addition while leaving the older miscount standing. I left it
untouched and propose the true-up below.

## Proposals

- **What:** True up the §3 Watches preamble's source enumeration —
  either recount per source arc or collapse it to "sources named
  per entry" and move attribution into the entries that lack it.
  **Why:** The enumeration (10) disagrees with the list (14); it
  went stale across at least four additions and will keep drifting
  as long as it double-books what the entries could carry
  themselves. **Scope hints:** `claude/MASTER.md` §3 only; a
  one-paragraph edit riding any next MASTER.md-touching session.
