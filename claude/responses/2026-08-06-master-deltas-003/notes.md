# notes.md — 2026-08-06-master-deltas-003

Deltas landed as enumerated. A few readings and one deviation worth
your eye at review; every changes[] path is inside the declared
scope, so nothing needs apply-time admission.

## The version true-up

The shipped `bin/bale` constant reads **0.3.34** (line 224), and this
request's own provenance stamp agrees (`bale_version: "0.3.34"`) —
the brief's don't-trust-the-guess instruction was warranted, since
the old §2 paragraph still said 0.3.32. The per-session split in the
new trail (0.3.33 at handoff-covering-001, 0.3.34 at
sweep-json-stats-002) is arithmetic — two code sessions after 0.3.32
under the cadence ruling, endpoint verified — not something I could
read from any shipped artifact. The §2 wording says so explicitly. If
either B session actually landed unbumped and something else bumped,
that sentence is the thing to correct.

## Deviation: the fold-in registry's json-sweep entry

The brief's untouched list ("run_hook f-strings, revert staging-row
rendering, label-column cap, BALE.md §13 sweep, internals-doc
true-ups") omits the existing "additive json `sweep` object plus
stats read side — rides board 10" entry, and B2 landed exactly its
write side. Leaving it unannotated would have contradicted the new §6
entry 56 in the same file, so I appended a dated bracket to it
(landed at B2; read side deferred with the stamp question, now a §3
watch) rather than forcing the untouched reading. Revert that bracket
if you'd rather the entry stand verbatim until board 10 disposes of
the read side.

## Tension: the §7 suite landmark vs. the standing no-counts sentence

The cargo pins recording 232 tests in §7; the same §7 bullet's
standing sentence says "neither counts nor per-file lists belong here
(both went stale within sittings)." I landed the pin exactly as
enumerated — claim-marked, dated, not re-verified — and left the
standing sentence byte-stable per the no-wording-improvements
constraint, so the two now coexist. If the claim-marked dated
landmark is the sanctioned exception, the standing sentence may want
a carve-out clause at the next MASTER.md touch; if not, the landmark
is the line to drop.

## Readings you should be able to confirm without the diff

- **Entry 54's resolution is an appended bracketed closing note**, the
  file's own convention (entries 44 and 46), not a rewrite — I read
  the prior-entries-byte-stable constraint as no-rewrites, with dated
  bracketed appends being the deltas shape's sanctioned resolution
  mechanism. Entry 25 itself stays untouched; its fourth tally is
  recorded on board 13's row and in entry 57, where the cargo put it.
- **ADR-0009's appended line omits "recognizing exercised practice."**
  The 0002–0004 flips recognize the harness that already runs under
  their rules; 0009 defers a doc — nothing was exercised. I read the
  brief's "same citation" for 0009 as the sitting citation only. One
  word to add to the appended line if the fuller phrase was intended.
- **0004's extra sentence rides the same single appended line**, so
  the diff stays inside DOCS.md §9's sanctioned flip shape (status
  line + one appended dated Notes line); same for 0009's
  armed-trigger clause.
- **The header's last-landed-by line was updated** to this sid — the
  cargo doesn't name it, but the header's own convention says it is
  edited in place at each landing.
- **§3's operator-friction bullet is gone**, absorbed by the rewrite:
  the sitting-closed bullet records the fold-in (state legibility
  onto board 10) and board 10's row carries the folded item.

## Validation shape

The ADR checks use evidence 35's reverse-transform pattern:
reconstruct the pre-change file from the staged bytes (un-flip the
Status line, drop the appended line) and require sha256 equality with
the request's shipped copy, hashes embedded at build time. The INDEX
Accepted-count check normalizes wrapped prose before counting — the
naive single-line grep false-negatived on ADR-0006's wrapped "Status:
/ Accepted" entry during my dry run, which is evidence 28's class
catching itself; the MASTER anchors are all deliberately single-line.
Claims cover these session-specific assertions per §5.3's
no-project-checks rule — a doc session does not run the suite, per
the brief.
