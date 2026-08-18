# notes.md — 2026-08-18-sitting-close-deltas-007

Base pin verified before any edit: the shipped `claude/MASTER.md` is
2805 lines, sha256 `d86703bd…f55095`, exactly matching the brief's
desk-verified pin. All block text was extracted mechanically from the
brief's BEGIN/END markers (and, for Block B, its `> `-quoted regions),
never retyped; the build script asserts the brief's quoted old texts
agree with what it found in the base, normalized, before replacing
anything.

## Placement latitude calls (per the flag-everything rule)

- **Block F placement.** Appended directly after the registry's last
  bullet (the Board 10 escalation-charge annotation), immediately
  before the "Landed 2026-08-05, non-board" dated paragraph, keeping
  the registry's existing tight structure — the base has no blank
  line between the last bullet and the first dated paragraph, and I
  didn't introduce one.
- **Block G placement.** Appended after the smoothing-sitting block's
  last line, separated by one blank line, with one blank line before
  `## 4. The board` — matching the §3 dated-block separation
  convention exactly as the base uses it.
- **Blocks C/D/E re-wrap scope.** Each conversion re-flows from the
  first affected line through the end of the containing paragraph
  (for E that means the rest of the telemetry-disposal bullet), at
  the *local* column convention: the 2026-08-16 §5 blocks wrap at
  ~72 columns, not the file-wide ~70, so the replacements match
  their neighbors. Content outside the replaced sentences is
  byte-identical after whitespace normalization — only line breaks
  in the re-flowed tail moved. Sids stayed unbroken (asserted).
- **Block A and F/G wrapping.** Landed at the brief's own wrap —
  Block A's 4-space continuation matches the two-digit board-row
  convention, F's 2-space continuation matches the registry bullets,
  and no landed line exceeds 79 columns (asserted; the widest are
  the §5 region's ~72-column lines).
- **Header edit.** `Last landed by:` set to this session's manifest
  `session_id` (`…-007`), edited in place; the stale `…-002` sid
  appears nowhere in the landed file (asserted).

## Validation design

The brief's negative-test requirement ("every containment and header
check must FAIL against the unedited base") is implemented as a
**reverse transform** (the evidence-35 reference pattern): the script
reconstructs the base from the landed bytes by inverting each of the
nine edits (each inverse replacement asserted to occur exactly once),
asserts sha256 equality with the pinned base hash — which
simultaneously proves the diff is confined to exactly the sanctioned
shape — and then runs the containment, phrase-count, and header
checks against the reconstruction, requiring each to fail there. The
base never ships in the response; the reconstruction is derived. All
matching is wrap-tolerant (whitespace-normalized), per the ratified
desk rule from the close-005 HOLD.

I additionally dry-ran the shipped `validation.sh` against the real
unedited base bytes before packing: all five claimed checks FAIL
there (containment names all six blocks missing; absence reports the
phrase count of 3 the brief states; the header check fails on the
`…-002` sid), exit 1. Against the landed tree: six PASSes, five
`[agree]` reconciliation rows, exit 0. The claims therefore carry
`claim_basis: "observed"`.

One check is run-but-unclaimed by design: the utf-8 decode is
file-syntax-mechanical (TARBALL.md §5.3's tautological class), so it
appears in `validation_will_run` but not in `claims`.

## Scope and cadence

Write forecast honored: `claude/MASTER.md` is the only change; no
out-of-forecast paths, nothing proposed into `out_of_scope` (the
request declares none). Doc-only landing — no VERSION bump shipped,
per the cadence ruling the brief restates. No INDEX.md change: no doc
was added, moved, or removed.
