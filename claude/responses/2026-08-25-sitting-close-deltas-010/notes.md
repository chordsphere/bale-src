# notes — 2026-08-25-sitting-close-deltas-010

Worker landing of the continue-plan-003 desk's sitting-close deltas
into `claude/MASTER.md`. The README brief was the complete, ratified
delta list; the manifest goal is its compression. One file, in
forecast — no out-of-forecast paths, so nothing here to admit at
apply.

## Role framing

This is a worker response session, not a sitting. The sitting ran at
the master desk (`2026-08-25-continue-plan-003`); I landed its output
per the brief. Per PLANNER.md's META, a worker building a response has
a mandatory read of zero on PLANNER.md, so it stayed unread past the
role check. Triggered contract reads before producing: TARBALL.md
(core), DOCS.md (in-place doc edit — no renumbering per §6.4, no new
doc/ADR/category, no whole-doc prune). CLAUDE.md core was read first.

## The three clarifications (asked before building; answers landed)

- **A1 — the board-51 "dissolve".** There was no fold-in registry
  entry to remove; the conditional lived in board-51's session
  Proposals, and the brief's "dissolve" wrongly implied a registry
  entry. Landed as a record-only clause on the rider-008 recording in
  the §3 landed-block: the board-51 conditional resolved moot — the
  pair landed as 0.4.16, so the shipped description string was already
  correct, and there was never an entry to strike. No add-then-strike.

- **A2 — the §7 suite counts.** The §7 Tests entry's own rule ("neither
  counts nor per-file lists belong here") governs over the brief's
  "582 cases" phrasing (you ratified treating this answer as the
  brief's correction). Landed the durable facts plainly — the
  `BALE_TEST_SLOW` gate/home, the `[INFO]` surface, the ~72% wall
  ratio, and the un-decorating recency watch — and rode the counts
  only as a dated basis figure marked "not a standing count," matching
  the runtime entry's "376 tests at measurement" precedent.

- **A3 — evidence 80's owe-note.** Updated in place: board 50 struck as
  swept-this-close (dated bracket), board 39 left owing. Leaving it
  stale while landing the very sweep it names would have been evidence
  80's own failure class committed inside evidence 80.

## Flagged convention edits (ratified via the heads-ups; look here)

- **Header last-landed-by → `-010`.** The doc's standing convention
  ("edited in place at each landing"); the `-009` collision session
  landed nothing and NNNs don't recycle on unlock, so this landing is
  `-010`. Precedent for why it matters: a prior 004-landing left the
  header stale and it was logged as a miss (§3 record).
- **Board 52's DONE bracket records the preamble-doctrine sweep as
  discharged out-of-forecast.** Board 52's row carries a "sweep any
  hand-carried-preamble doctrine (evidence 80's rule)" obligation. I
  checked MASTER.md and found no stale in-doc target: §5's 2026-08-18
  paste-block contract already states the post-52 residual correctly,
  and the doctrine edit that mattered landed at the rider in
  `docs/CLAUDE.md` (bale-emitted opener since 0.4.16) — outside this
  doc's forecast. Recorded the disposition in the bracket rather than
  silently treating the obligation as absent.

## Verbatim-required strings

The three marked phrases are landed byte-exact and self-checked in
`validation.sh`, matched **wrap-tolerant** (whitespace runs collapsed
before a fixed-string compare) because MASTER.md hard-wraps at ~72
columns — the document's own "probe phrases are matched wrap-tolerant"
convention. The phrases: the board-51 ambiguity clarification ("…
**cannot separate** …"), the bundle-stem remedy ("… **desk-unique
bundle stems**"), and the un-decorating recency watch ("… **un-decorating
is the named first-line remedy**"). One placement fix during the
build: the bundle-stem phrase was momentarily capitalized at a
sentence start; restructured so it lands lowercase-verbatim as marked.
`grep -c 'sed -i'` is 0 after the retirement, with the WSL and
Downloads-path facts retained.

## Re-delivery (wrap-trap specimen)

Re-delivered after the blind checkpoint's two verbatim-phrase probes
HOLD'd: the committed oracle pins "cannot separate" and "un-decorating
is the named first-line remedy" as contiguous byte spans, and they had
landed hard-wrapped — a wrap-trap specimen from the authoring side (the
brief dropped the never-wrap instruction the rider brief stated, the
class evidence 28 anticipated), fixed by unwrapping just those two
phrases onto single lines (house style tolerating the long line per the
rider precedent) with every other byte left as shipped. Flagged
deviation on the fix: `validation.sh`'s verbatim check is hardened to
assert single-line contiguity (raw `grep -F`) for the two oracle-pinned
phrases alongside the wrap-tolerant presence check, so a re-wrap of a
line-pinned span now fails my own hypothesis test rather than only the
oracle's.

## Claims / validation

No project lint, typecheck, build, or test surface applies to a
markdown doc, so per TARBALL.md §5.3 `claims` covers the response's
session-specific assertions (§7.2 item 6). All eight are claimed
`pass` with `claim_basis: observed` — I ran `validation.sh` against
the exact mirror bytes (sha256 matches the manifest) and the
reconciliation printed `[agree]` on every one.

## Look-closely on review

- The new §3 landed-block's voice and the four DONE recordings against
  the README content (§3 fold-in registry consume/add are mirrored in
  the registry list and named in the block).
- The §7 suite-facts bullet's count rendering (A2) and the version
  landmark's parenthetical (board 50 → 0.4.15, 51/52 bumpless, rider →
  0.4.16); the per-bump trail otherwise stays in git per the existing
  §7 convention.
- Board 55's cross-reference to §6 entry 85, and entry 85's
  cross-reference back to board 55.

## Proposals

None. The successor-surface-parity item is recorded as a
deliberately-unscheduled fold-in registry entry per the brief (a desk
disposition, not a worker-surfaced proposal), and the next-desk
sequencing lives in the landed-block's closing agenda line.
