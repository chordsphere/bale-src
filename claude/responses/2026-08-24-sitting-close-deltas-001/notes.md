# notes.md — 2026-08-24-sitting-close-deltas-001

Clean landing; nothing surprising in the base doc. Three things worth
finding without reading the diff:

- **Sid substitution.** The brief's sequencing precondition held: the
  shipped context carries
  `claude/telemetry/2026-08-18-submaster-doctrine-010.json`, so the one
  `<SID-SUBMASTER>` token in Block A became
  `2026-08-18-submaster-doctrine-010` (inside the backticks the brief
  already placed).

- **Re-wraps, and where they happened.** The brief's blocks were
  extracted mechanically, never retyped. Blocks C, D, and E landed
  byte-for-byte. Blocks B, F1, and F2 target indented regions (the
  row-49 4-space continuation; the registry bullets' 2-space
  continuation), so each was re-wrapped to its region's indent at width
  72 per the brief's wrap instruction; in Block A, only the bullet the
  sid substitution lengthened was re-wrapped, since the real sid is ~20
  characters longer than the placeholder. Every re-wrap was asserted
  token-stream-identical (whitespace-normalized) to the brief's text at
  build time, and `validation.sh`'s block checks are
  whitespace-normalized for the same reason — wrap-blind by
  construction, with each block checked together with its brief-named
  pre- and post-anchors, so presence and placement are one assertion.

- **Claims are observed, not predicted.** The three claimed
  session-specific assertions carry `claim_basis: "observed"`:
  `validation.sh` was executed against the built `files/` mirror in a
  simulated staging before packing, all checks PASS. In real staging
  the reconciliation block will also run (it skips here for lack of
  `.bale-manifest.json`, with the skip printed).

No out-of-forecast paths: the sole `changes[]` entry is
`claude/MASTER.md`, the request's resolved scope. `out_of_scope`
(docs/, tests/) untouched.
