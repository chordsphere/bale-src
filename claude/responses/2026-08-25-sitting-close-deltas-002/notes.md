# notes.md — 2026-08-25-sitting-close-deltas-002

Clean landing: all six blocks placed at their verified-unique anchors,
token-stream identity holds per block and whole-file, and the reverse
transform reconstructs the shipped base byte-for-byte (sha256
equality). Everything below is flagged latitude or observation, not
trouble.

## Decisions (flag-everything; latitude calls as shipped)

- **Strict greedy joined Block C's opening line.** The brief's
  displayed wrap puts the sid on its own second line; strictly greedy
  at 72 fits `[2026-08-25: 49b DONE —` plus the backticked sid on one
  71-char line, so the landed bracket opens with both. I calibrated
  the wrapper against the close-007-landed 49a-ii block first (it
  reproduces those 51 lines byte-for-byte, width counted in
  characters, em dashes = 1), so I followed the ratified practice
  over the chunk's display. Token-stream identity holds either way;
  the seam was mine per the brief.
- **Block E's pinned tail rode the final re-wrapped line.** The
  trailing clause `the per-bump trail —` stayed byte-identical and
  kept its base position as a suffix of the span's last line (54
  chars, under 72); everything from it onward is untouched bytes —
  the reverse-transform check would have caught any drift there.
- **Block B landed as paragraph + blank + six stacked list entries**,
  mirroring the chunk's own structure and the section-3 landed-block
  convention (close-004's ratified seating). Its line count differs
  from the brief's display (48 vs 52) only because the brief displays
  chunks at 4-space indentation while the landing re-wraps at the
  block's own indents — token streams are identical.
- **D1's bracket and D2's four entries landed contiguous, no blank
  lines**, per the registry's consumed-bracket convention; the
  `- Board 10 escalation-charge` entry follows D2 directly, as the
  anchor prescribed.

## Look here first

- The fixture-defect class caught in my own oracle, worth a line for
  the ledger's authoring-practice stream even though it never left my
  desk: my first-draft D1 assertion collected bracket lines until a
  line *ending* in `]` — and D1's own text contains the literal
  `[probe]` at a line end, so the collector terminated early and
  FAILed a correct landing. The same wrap-content hazard family as
  the wrap-blind grep and the date-pinned sid pattern. Fixed by
  making the collectors token-count-driven (C and the reverse
  transform got the same treatment prophylactically); the shipped
  validation.sh passed 8/8 against staged bytes and FAILs 8/8 against
  the unchanged base — the discrimination run the brief required.

## Validation account

Built programmatically per the brief: chunks extracted from the
shipped brief bytes (never retyped), transformations applied by
script, per-block and whole-file token-stream assertions
(old stream + exactly the six transformations = new stream) run at
build time; validation.sh independently recomputes placement,
per-block token identity, wrap discipline, and the reverse-transform
sha256 equality against the staged bytes, with the crafter's
reconciliation epilogue closing it out. Claims are all
`observed` — the staged run above is the observation. The registry
state was honored: the base carries neither this session's sid nor
the 49b session's record (stale-queue check ran before building),
and the one open session is the read-only master, disregarded as
structurally race-safe per its `[]` forecast.
