# notes.md — 2026-08-13-board-10-closeout-deltas-003

All seven brief items landed; the five anchor phrases are in the file
verbatim and unwrapped, and `validation.sh` asserts each one plus the
absence checks, so the checkpoint and my script are approaching the
same contract independently. Three places where I mapped the brief's
mechanism onto the file's structure, and two inferences you should
glance at:

## Mechanism → structure mappings (the ratified wave-1 reading)

- **Item 2's "0.4.7 live."** §3's bullet keeps "the version position
  is §7's, its one home" — I did not put a version number in §3. The
  0.4.7 position lands via §7's landmark (item 3), which is where the
  collapse ratified 2026-08-07 says it lives. Everything else in item
  2 landed in §3 as written: the wave 2–4 sids on latest-applied
  (plus the wave-1 deltas sid, since the brief counts that landing as
  wave 2), and the escalation-contract wire-format line.
- **Item 4a's figure.** The watch is cleared (removed) and the
  measured figure recorded in §7 as a standing environment fact,
  since that's the only home the file offers for an operator-side
  runtime landmark. §7's tests bullet forbids standing suite counts,
  so the "376 tests" rides as dated at-measurement provenance,
  explicitly marked "a dated figure, not a standing count." The range
  is written "60.8–63.1s" with 60.8 first, per the brief. If you'd
  rather the count not appear in §7 at all, deleting the
  parenthetical is a one-line follow-up — the anchor is the 60.8, not
  the count.
- **Header last-landed-by line.** Not on the edit list, but the
  header's own convention says it is edited in place at each landing;
  it now names this sid. Flagging since the brief said change nothing
  not listed.

## Inferred attributions (item 4b) — look closely here

The stale preamble arithmetic claimed 10 entries against a list of
14, so positional attribution no longer resolved for two entries.
What I did:

- The first four entries (emitter-parser, tag-reuse, mixed `at`,
  closure-mix): attributed to the board-5 arc's upward report —
  positionally solid, "the first four" is unambiguous.
- Removed-oracle, `[validation]` layering, required-set keyed form:
  attributed to the board-6 arc's report. The first two already cited
  board-6 artifacts inline (session C's note, the rev B brief's D1);
  **required-set is the inference** — its subject (`[validation]
  required`, ledger `[SKIP]` rows) is board-6 material, but I could
  not verify which document it was carried from. Correct it if the
  provenance is elsewhere.
- Plan-less handoff friction: attributed to the handoff-covering
  landing (`2026-08-06-handoff-covering-001`) — **also an
  inference**: the watch describes exactly that session's behavior,
  and board-35 session 3's ratified line references it as "the
  standing watch," so it predates 2026-08-07. Correct if it actually
  came via a report rather than the session's own notes.
- The remaining entries already carried their sources inline
  (auto-sweep-009, §6 entry 56, board-13 brief I.6, board-13b's
  archived notes); I left those as-is rather than duplicating.

The arithmetic prose does not survive anywhere: `validation.sh`
checks the normalized (line-joined) text for both the prose and
numeric forms, per the DOCS.md §9 normalization rule.

## Small readings worth confirming

- "Judgment calls for all four" in the board 10 row: I read "all
  four" as the four wave 2–4 sessions the brief lists (network
  grant, wave-1 deltas, telemetry extensions, escalation schemas).
- Item 1's "Remaining" line replaces the old "Remaining sequence: S2
  → S5 → S4 …" sentence wholesale; §3's pointer now says "the
  remaining S7 → S6 sequence."
- The wave-1 agenda bullet ("Per-session blind checkpoints") is
  untouched even though S7 now owns its near-term half — annotating
  it was outside the edit list. If you want the cross-pointer, it's a
  one-line rider on the next MASTER.md touch.
- Evidence numbering verified against the file, not the brief: max
  was 64, new entries are 65–67 under a sitting header matching the
  wave-1 convention ("New from the board-10 wave 2–4 sittings
  (2026-08-12/13):").

## Claims

One claim, annotated form: the session-specific assertions are
claimed `pass` with `claim_basis: "observed"` — I ran the exact
script against a staging-shaped copy of the shipped tree before
packing and every assertion passed. File sanity is listed in
`validation_will_run` but unclaimed (mechanical, tautological). No
project-level checks run for a MASTER.md-only doc change; per the §5
contract, claims cover the response's own assertions. Doc-class,
bump-exempt: no VERSION change shipped, consistent with the trail's
"no bin/bale ships here" recording.
