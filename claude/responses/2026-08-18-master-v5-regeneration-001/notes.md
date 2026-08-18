# notes.md — 2026-08-18-master-v5-regeneration-001

## Retry (corrects the same sid's first response)

The first response HELD on the blind checkpoint's `landmark-current`
probe: a fixed-string grep for `0.4.11 at`, the brief's own
parenthetical shape, which my condensed §7 sentence paraphrased as
"0.4.11 (landmark: `sid`...)" — same content, different phrase
shape, so the probe missed. Bale itself is still 0.4.11 (desk-
verified), so the landmark's substance was never stale. This retry
changes exactly one thing against the held branch: the §7 landmark
parenthetical now reads "bin/bale VERSION 0.4.11 at
`2026-08-16-planner-injection-wiring-006` (the five-doc injection
wiring, the current landmark)". Nothing else differs — every other
byte of both files is identical to the held commit. The checkpoint
was disclosed in chat at the desk's inspection, so it is no longer
blind to this session; I replicated it verbatim and ran it against
the retry bytes in simulated staging before packing: all 22 probes
pass, exit 0. Worker validation also re-ran green after the edit
(the landmark sentence sits in the §7 Repo bullet, whose kept parts
are substring-asserted; no assertion pinned the trimmed
parenthetical's wording, so no validation change was needed beyond
regeneration).

One observation for the checkpoint pattern, not a complaint: the
2026-08-16 desk rule makes probes wrap-tolerant, but a fixed-string
probe for a phrase the worker is expected to *author* (rather than
preserve) is sensitive to legitimate paraphrase — the brief said
"condenses to the current landmark (0.4.11 at `sid`)" and I read
the parenthetical as content, not as pinned phrasing. Where an
outcome probe greps for authored-not-preserved text, either the
brief marks the phrase verbatim-required or the probe targets the
invariant (e.g. the version string and the sid co-occurring)
rather than the connective. Filed under Proposals below.

Base identity verified before editing: the shipped
`context/claude/MASTER.md` hashed
`ffcec2d8839c65260569f04ab14f8735d54549e907105d0bec10ea1a32c818f8`
at 3063 lines, matching the brief's pin. The transform was applied as
line-range replacements against that copy (never retyped through
context), each anchored on a loud prefix assertion. Result: 2574
lines. Every preservation claim below is enforced mechanically in
`validation.sh` against hashes derived from the base bytes at build
time — whitespace-normalized region hashes plus substring assertions,
never single-line greps (the wrap-blind-grep lesson honored).

## Pruned and condensed blocks, enumerated (reconciled against the diff)

Durable-home key: **git** = v4 of MASTER.md in git; **telemetry** =
the sids' records under `claude/telemetry/`; **notes** = the sids'
archived notes under `claude/responses/`.

R1 (header): title line to v5 — 2026-08-16; supersession sentence now
v5-supersedes-v4; last-landed-by set to this sid. The going-forward
convention paragraph and the this-document paragraph are verbatim
(substring-asserted), including the convention's "effective v4"
wording, kept as written per R1.

R2 (§2): the "v4 regeneration (this compression sitting's record)"
block (base lines 122–142) condensed to the one-paragraph
regeneration record covering v4 and v5 — dates, authoring/landing/
ratification sids for v4 including the board-33 correction, this
session for v5. Displaced narrative (the deltas-vehicle framing, the
012 compaction disclosure, evidence-46/47 pointers, the correction
bracket): git. All other §2 paragraphs, the arc summaries and the
Current-version landmark paragraph included, are verbatim
(region-hashed).

R3 (§3 head + watches): untouched, region-hashed.

R4 (fold-in registry): exactly two entries pruned whole, both
carrying dated discharge brackets — the reconciliation
label-column-cap entry (base 284–293) and the crafter
epilogue-separable-fragments entry (base 324–336). Durable homes:
git, plus the implementations and pinning tests they name
(`2026-08-15-doc-mechanization-002`). Every other entry is verbatim,
verbatim-quoted proposal text included (region-hashed with the two
pruned ranges excised from the expected). Note: the additive-json
`sweep` entry's dated bracket is a partial discharge with a live
deferral, not a discharge bracket, so that entry stays whole per the
brief's exactly-two enumeration.

R5 (§3 tail): the seven "Cleared at …" paragraphs (base 498–548,
six at-this-landing plus one at-the-v4-regeneration) deleted whole —
git holds them; validation asserts the count at zero. Five dated
blocks before 2026-08-13 condensed to one line each keeping date,
sids, and the brief's pointer sentence: the 2026-08-05 auto-sweep
landing + its four ratified calls (git; notes; the sweep standing
fact itself is live in §7 verbatim); the 2026-08-06 board-34 calls
(seven bullets → git/notes); the 2026-08-07 board-13 calls (thirteen
bullets), the 2026-08-07 sandbox/board-35 calls (thirteen bullets),
and the 2026-08-07 close-deltas/pack-guards calls (eleven bullets) —
all git/notes. Everything dated 2026-08-13 and later is verbatim
(region-hashed). The cutline read cleanly against the bytes — no
block straddled it, so nothing needed flagging under the
flag-don't-rework rule.

R6 (board, per-row treatment):

- Condensed to identity-preserving one-line pointers (number, bolded
  title, terminal status + date, sids, telemetry pointer; displaced
  narrative → git, per-session facts → telemetry/notes): rows 1, 2,
  3, 4 (pre-telemetry rows point home: git), 5, 6, 7, 8, 12, 13, 14
  (no sid; chat-ratified, evidence 32 kept as its pointer), 15 (both
  sids kept — the landing and its same-sitting follow-on), 16, 17
  (the "rode 22a" linkage kept), 18, 19, 20, 21, 22 (sub-identities
  22a–22d kept with their sids; the mechanize-shape §5 pointer
  kept), 23, 24, 25, 26, 27, 28, 29 (the 28/29 fusion kept on both
  rows), 30, 31, 32, 33, 34. Arc rows 6 and 13 point at their
  committed arc-artifact directories; arc rows 5, 22, 34 list sids
  (no path-stated arc home in the doc for 5; 22 and 34 are
  sid-shaped).
- Row 33 additionally rides its 2026-08-03 sentinel-literal hazard
  bracket verbatim, per the brief. **Flag, not a rework:** the
  bracket's premise sentence ("this row's own spec line carries the
  literal it names inline") is stale post-condensation — the spec
  line is gone and the sentinel literal now appears nowhere in
  MASTER.md (validation asserts its absence). That moves the hazard
  in the safe direction (the doc can no longer trip a widened
  refusal), arguably to vacuous. Kept verbatim as instructed;
  dropping or rewording the bracket is the desk's call at a future
  touch.
- Row 5's "presumed-landed-with-005" bailout-banner inference note
  (recorded-as-inference-not-fact) condensed away with the rest of
  the row's annotation dispositions; the claim and its caveat travel
  to git together, so no inference was silently upgraded. Flagged
  here in case the desk reads that note as live residue — kick back
  if so.
- Verbatim (region-hashed): rows 9, 11, 36–46; row 10 except the one
  sub-entry below; row 35's head + ranked gap list and its
  Remaining-queue residuals paragraph (the three live queued
  residuals ride there).
- Row 35's four Session paragraphs condensed to one-line pointers
  (sid; telemetry). Displaced per-session detail (census locations,
  queue-addition narratives, the ~111s/323-test figures): git +
  notes; the live ~111s margin also stands verbatim in the §3
  --slow watch.

R7 (row 10 planner-doctrine sub-entry): condensed to the short
record — queue name, lifted-to-§5 pointer, the two execution sids
with their one-line facts (S6 inherits ratify-and-churn; injection
wiring at 0.4.11), and a git pointer for the pre-execution inputs
and charter working copies. This deliberately supersedes the
"board 10's queue entry keeps the working copies" call, per the
brief. **Consequence, proposed not made:** §5's 2026-08-16 block
(untouched — §5 is out of scope) still says "board 10's queue entry
keeps the working copies, bracket-annotated as lifted", which is now
stale against the board. A one-clause true-up there is queued for
the next §5-touching session; board 46 or a sitting-close deltas
vehicle are natural carriers. The rest of row 10 — the S6 agenda
blocks, all Added blocks, the DISCHARGED-EARLY promotion bullet with
its lifted-to-§5 bracket — is verbatim (region-hashed in two pieces
around the sub-entry).

R8: §5 and §6 untouched entirely — region-hashed whole, evidence
numbers and contract blocks bit-identical modulo nothing (the hash
regions cover them end to end).

R9 (§7): two trims exactly. The version trail condensed to the
0.4.11 landmark — phrased "0.4.11 at
`2026-08-16-planner-injection-wiring-006`", the brief's own
parenthetical shape — plus one
sentence pointing the per-bump trail and the bump-exemption record
at git and telemetry; displaced with it: the 0.4.3-and-earlier
verification provenance and the trues-them-up sentence (the standing
sitting-open `bale --version` rule lives on verbatim in §2's
Current-version paragraph; one-apply-behind lives on in its own §7
bullet). And the dated "(4,111 lines after the 8a/8b/8c arc)"
parenthetical dropped from the module list — the whole parenthetical,
since the arc attribution is meaningless without the figure; the
module list itself, the bale_stats claim bracket, and the load-time
import-set guidance (evidence 13) are verbatim (substring-asserted).
All other §7 bullets verbatim (region-hashed in two pieces around
the Repo bullet).

R10: `claude/INDEX.md` — exactly one line changed: "(v4 as of
2026-07-31)" → "(v5 as of 2026-08-16)".

## Look closely

- The condensed one-line pointer texts and the regeneration-record
  paragraph are the only new prose in the file; everything kept is
  mechanically pinned to the base. Review the new prose; the machine
  vouches for the rest.
- Line-wrap on kept content: replacements preserved kept lines
  byte-identical except the two §7 re-wraps forced by the trims (the
  module-list lines and the row-33 bracket's first line re-flow);
  those are whitespace-normalization-identical, which is the
  invariant's own bar.

## Proposals

- **What:** for future blind checkpoints, split probe targets by
  provenance: preserved text may be pinned as fixed strings (the
  worker must carry it byte-verbatim anyway), but authored text —
  condensation pointers, new records — gets either a
  verbatim-required marker in the brief or an invariant-shaped
  probe (co-occurrence of the version string and the sid) instead
  of a connective-phrase grep. **Why:** this session's only HOLD
  was a paraphrase of a phrase the brief presented as content;
  the outcome the probe guarded (landmark present and current) was
  true in both responses. **Scope hints:** PLANNER.md's checkpoint
  authoring guidance; no bale code.
- **What:** true up §5's 2026-08-16 block: replace "board 10's queue
  entry keeps the working copies, bracket-annotated as lifted" with
  a clause noting the queue entry now condenses to a pointer and the
  working copies live in v4 (git). **Why:** this session executed
  the brief's sanctioned supersession of that call, and §5 — out of
  scope here — now describes a board state that no longer exists.
  **Scope hints:** one sentence in `claude/MASTER.md` §5; a natural
  rider on board 46's doc-deltas carrier or the next sitting-close
  deltas session.
- **What:** at the next touch of board row 33 (or a sweep), decide
  whether the ridden 2026-08-03 hazard bracket should be retired.
  **Why:** its premise is stale post-condensation (see R6 above);
  the sentinel literal no longer appears in this doc, so the hazard
  it records may now be vacuous. **Scope hints:** row 33 only; a
  one-bracket edit.
