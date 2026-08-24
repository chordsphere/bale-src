# notes.md — 2026-08-24-sitting-close-deltas-007

Clean landing: one file, five blocks, all payload text carried from
the brief programmatically (extracted from the shipped README.md's
indented chunks, never retyped), whitespace-normalized, and
greedy-rewrapped at width 72. Token-stream identity held per block
and for the whole file — the build asserted that the new file's
token stream equals the old file's with exactly the five specified
transformations applied, and validation.sh recomputes normalized
token-stream and placement assertions against the staged bytes. The
brief's stale-brief guard heading matched (revA, the 49a-ii
sitting), all five anchors resolved uniquely against the shipped
file before I built, and `<SID-SELF>` substituted as this session's
sid from the manifest. Per the registry-state note, the one open
session is the read-only master (forecast `[]`) — structurally
race-safe, disregarded. Doc-only, so no VERSION touch per the
cadence ruling. The single `changes[]` path is in-forecast; nothing
is out of forecast and nothing was deferred.

## Decisions

Flagging the latitude calls for ratification, one each:

- **Block E's "trailing clause stays byte-identical" honored over
  full-entry greedy re-wrap.** I re-wrapped only the three lines the
  landmark span occupied and kept every following line of the entry
  byte-identical (from "every bump's sid…" on). Consequence: the
  seam line "landmark); the per-bump trail —" is shorter than a
  strict whole-entry greedy re-wrap would produce, because the
  untouched trailing lines pin the wrap boundary. Byte-identity of
  the trailing clause and strict greediness across the seam can't
  both hold; I chose the brief's explicit byte-identical
  instruction. The same local-re-wrap approach covered Block D: only
  the one anchor line reflowed (into two lines carrying the
  bale_open insertion), with every other line of the §7 entry
  byte-identical.
- **Block C appended with no blank line between brackets**, matching
  row 49's existing convention — its 2026-08-18 and 2026-08-24
  brackets stack on consecutive lines. "As a new bracket paragraph"
  read as a new bracket in that stacked shape, at the row's 4-space
  indentation.
- **Block B's internal blank line kept.** The payload carries a
  blank line between the header line and the first list item; the
  resumed-49 block it sits beside has the same shape, so the blank
  line landed as part of the block (token-stream identity is
  unaffected — the assertion tokenizes on whitespace).
- **Wrap seams are mine, not the brief's.** The brief's payload
  chunks carry their own line breaks (some short of greedy); per the
  re-wrap instruction I wrapped strictly greedy at 72 rather than
  preserving the brief's seams, so landed line breaks differ from
  the payload's while the token streams are identical.

## Look here first

The Block E seam described above — if the desk wanted the whole §7
entry greedy-rewrapped (trailing clause included), that is a
two-line diff to kick back; as shipped, the trailing clause is
byte-identical per the brief's letter.

## Validation basis

Both claims are `observed`: I ran validation.sh in a simulated
staging (base tree + files/ overlay + the manifest at
`.bale-manifest.json`) — all three checks PASS, both claims
reconcile `[agree]`, exit 0 — and also ran it against the unchanged
base to confirm the assertions discriminate (exit 1 at base, as a
blind oracle would want). The utf-8 check is mechanical and stands
run-but-unclaimed.
