# notes.md — 2026-08-15-claude-core-first-001 (r3)

Content bytes are identical to r2, which cleared your blind
checkpoint 15/15. This round exists to resolve r2's own HOLD —
my check 6 — and records the probe round per §4.5, since the paste
is chat-ephemeral.

## What the probe established (2026-08-15, main = 13d3740)

- Sibling `2026-08-14-global-doc-selfcontainment-006` landed
  between this session's first apply (base 6202940) and the retry
  (base 13d3740): +BALE.md section, +guard test
  (`tests/test_global_doc_selfcontainment.py`), and a 77-line
  rewrite of `docs/TARBALL.md` that strips project-local doc
  references (`BALE.md §…`, `orchestration.md §8`) into generic
  "the bale tool's own documentation" pointers — the injected-doc
  ruling this session's Job 2 sentence is the CLAUDE.md half of.
  §3.4 additionally gained the `--checkpoint-file PATH` row and a
  "Checkpoint-configured projects" paragraph.
- `docs/CLAUDE.md` is untouched between the two bases (diff count
  0) — the forecast gates held, as designed.
- No uncommitted drift under `docs/`; main == HEAD == 13d3740.
- Post-sibling §3.4 fingerprint, computed in your environment with
  the *same awk extraction check 6 uses*:
  `f5a36738fb404fae369fb2fe2fde8a9845e7dc658a2e478a2803f62cc0b47654`
  (151 lines). It matches the retry log's "got" value, confirming
  the check-6 failure was the sibling landing, not corruption. The
  probe ran under your explicit chat override of the request's
  `expects_probe: no`.

## What changed in r3

Exactly one thing outside prose: check 6's baseline constant is the
probe-established hash above, its failure message now names the
re-landing race, and its claim is upgraded `predicted` → `observed`
(the r2 `[DISAGREE]` on that row was the claims split doing its job
— the one claim I couldn't observe was the one that flipped).

## Pair coherence judgment (ratify)

The §11.2 ↔ §3.4 sanctioned pair survives the sibling's rewrite
**without propagation**, so my §11.2 side ships byte-identical
(check 5 still fingerprints it). Reasoning: §11.2's side of the
pair is by-reference — "form, flags, and their mapping to manifest
fields live in `TARBALL.md` §3.4", plus the `--supersedes`
split-supersession pointer — and every referenced element survives:
the flag surface is intact (edits were citation rewording; the new
content is additive), and the supersession flow's mechanics are
unchanged. The new checkpoint paragraph explicitly leaves the
worker-facing half in §7 ("this section does not restate it"), so a
worker-emitted §11.2 rescope command still never names a checkpoint
— `--checkpoint-file` is planner-delivered by construction, which
keeps the blind-authorship doctrine coherent from both ends. If you
read the pair more strictly — that §11.2 should now *mention* the
checkpoint precondition a pasted rescope command meets in
checkpoint-configured projects — that is a content change to §11.2,
out of this session's constraint ("relocation and trigger wiring
plus one added sentence only") and a candidate follow-up, not
something I'd smuggle into a correction round.

## Known race, accepted

One sibling is still open (`2026-08-14-improve-bale-005`, the
sitting this session came from). Its forecast is disjoint from
`docs/CLAUDE.md` but I can't rule out `docs/TARBALL.md`. If it
lands on TARBALL.md before this retry, check 6 fails again by
design and needs one more one-line re-baseline. I judged pinning
the exact bytes worth that risk over loosening the check (e.g.
existence-only), because the pair rule is byte-agreement, and a
check that can't see drift isn't guarding the pair.

## Carried from earlier rounds, still open for ratification

- "Re-read `TARBALL.md` in full" in §11.6 left alone (deliberate
  post-compaction prescription; survived 22a).
- r2's correction: pre-§11 prose names the core boundary by section
  numbers, banner literal unique file-wide, compaction INDEX row
  reverted to shipped verbatim.

## Proposals

- **What:** Harden the checkpoint template's banner locator to a
  strict line anchor (e.g. `^> \*\*PAST THE CORE`) rather than a
  first-match phrase grep.
- **Why:** The first HOLD came from a loose locator meeting an
  honest prose mention of the banner phrase. Content-side fixes
  removed the collision here, but any future core-first restructure
  whose brief wants the banner *named* in reading-order prose
  re-trips it. Checkpoint authoring is yours; flagging because the
  failure mode is structural.
- **Scope hints:** checkpoint scaffolds; independent of this
  session.

- **What:** Decide whether CLAUDE.md §11.2's rescope-offer prose
  should mention the checkpoint precondition that
  checkpoint-configured projects now put in front of any scoped
  pack (per the new §3.4 paragraph).
- **Why:** Today the pair coheres by §3.4's explicit deferral to
  §7, so nothing dangles — but a planner pasting a worker-emitted
  rescope command in this repo will hit the checkpoint refusal
  unless they've authored one, and §11.2 doesn't set that
  expectation. Whether that's a doc gap or working-as-intended is a
  planner call.
- **Scope hints:** `docs/CLAUDE.md` §11.2 (sanctioned-pair
  propagation rules apply — same-session twin check against §3.4);
  only after this session closes, since it shares the file.
