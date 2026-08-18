# notes.md — 2026-08-16-rider-foldin-deltas-010

## Check first on review

1. **Base identity was assumed, not verified.** The brief says the
   shipped MASTER.md's sha256 as packed is stated in the pack chat;
   that chat wasn't available to this session and no hash arrived in
   the preamble, so the before-editing comparison the brief asks for
   could not run. The shipped copy I edited against hashes to
   `3fb0222ea426c12061e7d19a26e97f2428d724c012ee53ad11a8eb23c7d47418`
   (stated in chat before building, per the recoverable-risk posture
   of TARBALL.md §3.3). Compare that against the pack chat's stated
   value before applying — a mismatch means this response edited a
   stale base and should be kicked back, not applied. This is
   exactly board 41's lost-update hazard, hand-checked because the
   gate doesn't exist yet.

2. **F2 was verified from the manifest stamp, not a VERSION file.**
   The brief says "the shipped VERSION file in this request reads
   0.4.11," but no VERSION file shipped — context/ holds only
   MASTER.md. The 0.4.11 fact was verified instead against two
   shipped corroborators: the request manifest's own
   `provenance.bale_version: 0.4.11` (stamped by bale at pack) and
   MASTER.md's §2/§3 records of the injection-wiring landing at
   0.4.11. Recorded as `includes_missing` in the feedback block —
   a packing signal, not a blocker.

## Latitude calls landed as written (009 desk; ratify at review)

Per the brief these are the 009 desk's calls, not open design; they
were landed exactly as written and nothing read wrong:

- Row numbering 41–46 (highest existing row was 40; no gaps reused;
  §6's evidence pile independently numbers into the 40s — different
  section, no collision within §4).
- Carrier and fusing choices inside the row texts (e.g. 41 adjacent
  to 39, 42 sequenced before-or-with 43, 43 gated on 42's
  docs_read).
- Queue framing "queued 2026-08-16" matching rows 36–39's pattern.

## Placement judgment calls

- **Block B** (row 37 bracket) starts on its own line at the row's
  4-space continuation indent — matching the own-line bracket style
  rows 10 and the fold-in registry use for dated annotations, rather
  than flowing mid-paragraph.
- **Block C** follows the row-10 convention of no blank line between
  an Added block and the preceding bullet.
- **Block D**'s intro paragraph and bullets sit at §5's standard
  0-indent/2-space shape, separated from the bad-oracle entry by one
  blank line, same as the section's other dated blocks.
- **F1's dated note** was appended as a new wrapped line inside the
  execution-context entry, immediately after its closing
  parenthesis and before the next bullet.

## Verification record

- Diff shape verified at build time against the shipped original
  (the staging copy can't see the pre-change file, so this check
  can't live in validation.sh): exactly 5 lines removed, all
  belonging to the three enumerated in-place edits (the header
  line, F1's four→five line, and F2's three touched trail lines);
  every other change is a pure insertion. 196 lines added/changed,
  none over 72 columns.
- Landed-vs-brief equality of blocks A–E, the F1 note, and the F2
  trail/range phrases verified whitespace-normalized at build time
  (the close-005 pattern), and the same checks ship in
  validation.sh with the expected texts base64-embedded from the
  brief's own bytes — never retyped.
- The brief's identity check ("pack report's echoed first heading
  matches this file's") could not run either — no pack report was
  relayed. The brief's own first heading names this pack's slug and
  the master sid, both matching the manifest, so the right brief
  resolved with high confidence.
