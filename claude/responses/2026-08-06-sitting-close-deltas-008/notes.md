# notes — 2026-08-06-sitting-close-deltas-008

All nine brief items (A1–A2, B1–B3, C1–C4, D) landed. Relay to the
master per the standing constraint. Nothing surprising in the work
itself; the items below are readings I made and two things worth a
close look.

## D — the branch taken

Expected branch confirmed: no project-name key exists in
walk_configurables today. I enumerated the walked keys in the shipped
bale_config.py — hooks.post_pack, hooks.post_apply_pass,
apply.search_paths / no_interact / hook_auto_accept / archive_dir /
sweep, staging.strategy / untracked_inputs, identity.packer,
validation.base / required (the last two project-layer only) — and
separately confirmed `manifest.project` is filled from `repo.name` in
bale_pack.py (build side at line 623, call site at 2622), matching
the sentence BALE.md keeps. So: pruned the stale sentence, claimed
nothing. For the board-15 doc-gap pile, as directed, one line:
whether a project-name key *should* exist in walk_configurables is
open — the config subsystem could carry one, nothing does today, and
BALE.md now simply doesn't speak to it.

## Readings I made (say if any is wrong)

- **A1's "bullet."** The suite-count landmark isn't its own bullet —
  it's a sentence span inside the §7 Tests bullet, after the named
  landmarks. I deleted exactly that span ("Suite landmark,
  claim-marked: 232 tests green ... does not run the suite).") and
  kept both the no-counts sentence (byte-stable, pinned in
  validation) and the trailing "ADR-0005 (Accepted 2026-07-28)
  governs." — the ADR pointer is about sandbox rules, not counts, so
  I read it as staying.
- **B3 citations.** The brief said compress-to-a-line, not verbatim,
  so I qualified the bare cross-doc numbers while keeping content:
  "TARBALL.md §7.4" for the checkpoint-argv and pass-through calls,
  "BALE.md §7.2" for the authorship-line prune. Inside MASTER.md the
  bare numbers would resolve wrongly — the same hazard the §13
  citation-qualification fold-in just cleared.
- **C2 formatting.** The two verbatim blocks are re-indented to the
  row's four-space continuation and the brief's `>` quote markers
  dropped (I read them as the brief's quoting device, not shipped
  bytes); every character of the text itself is unchanged, and
  validation pins anchors from both blocks.
- **B2's cleared entries.** I followed the registry's standing idiom
  for full clears — entries removed from the list, recorded in a
  "Cleared at this landing (`<sid>`)" paragraph — with the
  staging_error addition carried as a dated bracket inside it.

## Look closely

- **§2's version paragraph still reads "Current version: 0.3.34."**
  A2 named §7's landmark only, so I stayed in lane and left §2's
  paragraph untouched — but it now disagrees with §7's 0.4.0 and
  with the board-34 row. Its verification narrative ("read from the
  constant in the copy shipped read-only in this deltas request")
  even describes this request, whose shipped copy reads 0.4.0.
  Proposal below.
- **The verbatim handoff --verbose fold-in carries an unqualified
  "§5.4"** ("Recorded in §5.4's updated bullet..."). Inside
  MASTER.md that resolves to nothing sensible — it means BALE.md
  §5.4, per the worker's original context. Shipped verbatim as the
  brief directs; flagging it because it's exactly the class the
  citation-qualification work targets. Reported, not fixed.

## Proposals

- **True up §2's Current-version paragraph to 0.4.0.** What: rewrite
  the §2 "Current version" paragraph to 0.4.0 with the 0.3.35/0.4.0
  trail, or collapse it to a pointer at §7's landmark so the version
  lives in one place. Why: this session left the doc internally
  inconsistent (§2 says 0.3.34, §7 and the board say 0.4.0) because
  the brief scoped A2 to §7; two homes for the same live fact is how
  it drifted. Scope hints: MASTER.md §2 only; a natural rider on the
  next master-deltas or doc session touching MASTER.md.
