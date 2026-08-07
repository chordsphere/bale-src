# notes.md — 2026-08-07-board-13c-contract-docs-006

Doc-only session, both changes inside the forecast, zero drift to
enumerate. Per the close-out charge, the judgment calls between
defensible alternatives, with the rejected alternative named.

## Judgment calls

**The CLAUDE.md §6 bullet cites ADR-0015 by number.** CLAUDE.md
previously cited no ADR anywhere — only TARBALL.md carries
`(rationale: ADR-NNNN)` pointers. I added `(ADR-0015)` to the lane
bullet anyway, because the kernel's home should be findable from
the rule that elaborates it, and TARBALL.md's citation convention
is precedent that global docs may cite bale-src ADRs. Rejected
alternative: keep CLAUDE.md ADR-free and let TARBALL.md §3.2 carry
the pointer — defensible on purity grounds (CLAUDE.md is the *why*
doc and casual projects never see the ADR directory), but it makes
the one contract sentence that was formally ratified the one with
no provenance trail. Strip the parenthetical at review if you want
the old purity back; nothing else depends on it.

**Kernel elaboration, not quotation.** The bullet paraphrases the
ratified kernel rather than block-quoting it. The kernel's three
commitments are each present in order (forecast-is-the-ask /
ship-enumerate-admit-never-silently / never-onto-a-sibling's-path),
and the two proposed-never-made residues are stated exactly as the
brief narrows them. Rejected alternative: quoting the kernel
verbatim inside the bullet — it would survive drift-auditing
better, but the kernel's register (a Consequences bullet) doesn't
match §6's imperative voice, and the README says "your drafting
elaborates it, never contradicts it," which reads as license to
paraphrase.

**The convention paragraph's bold lead was renamed** ("Includes
name existing context; new files are the worker's call" →
"Declarations name existing paths; new files are the worker's
call"), since the rule now spans both flag families per brief I.1.
Bold-lead paragraphs are not numbered anchors, so §6.4 stability
doesn't bind, and I found no doc that cites the paragraph by its
lead text (ADR-0014's clause 2 title is its own append-only text,
untouched). Rejected alternative: keep the old lead and bolt the
`--write` sentence on — preserves greppability of the old phrase at
the cost of a lead that names only half the rule it governs.

**Sweep extent.** The charge licensed sweeping "any other sentence
in those two files that asserts includes gate concurrency." I read
the same-conflation class slightly wider than the literal
concurrency assertions and also trued up: the §5.4 enumeration
bullet ("no included directory covers" keyed coverage on includes),
the split-supersession paragraph's two "scope collides" phrasings,
and §8's gate-summary parenthetical ("worker-created new files
being the canonical case" — true historically, but it understates
the generalized drift class the revised doctrine rests on). All
are in-forecast and prose-only. Rejected alternative: literal-
minimalism, leaving those three sites for a later pass — cheaper to
review, but it ships a contract doc that teaches the old model in
§5.4 while teaching the new one in §3.2, which is the
docs-assert-the-opposite-of-the-tool trap ADR-0015's Notes warn
about.

**"scope" survives as a word.** I did not purge the term — the
registry record, the `resolved_scope` key, §8's "the scope gates of
§3.2," and "the scope is wrong" in the goal-row all keep it, since
ADR-0015 keeps "scope" as the name of the concept and changes what
the value *is*. The sweep targeted sentences that key scope on
*includes*, not the word itself. Rejected alternative: a full
vocabulary migration to "forecast" everywhere — it would orphan the
`resolved_scope` key name and every historical cross-reference for
no doctrinal gain.

**Version citations.** New text cites v0.4.1 for the separation
(session A's landing version per ADR-0015's Notes) and preserves
the v0.3.x history where rows already carried it (`--read-only`
keeps v0.3.15/v0.3.21 with the reinterpretation layered on). If
the desk dates the separation differently, the two "v0.4.1"
mentions in §3.2, one in the `resolved_scope` bullet, and the two
in the §3.4 rows are the sites.

## The `unknown` claim

`project tests (pytest, staging only)` is claimed `unknown`: tests/
was not shipped (it is session B's forecast) so I cannot know
whether any fixture asserts contract-doc content, nor even whether
the staging copy carries a runnable suite. What I would need to
predict: the tests/ tree, or a statement that no fixture pins doc
wording. The check is guarded — it SKIPs when tests/ or pytest is
absent — and if it *fails* at your apply, the failing fixture is
exactly the tests/-edit case the README pre-answered: I did not
touch tests/, so the fix lands via session B or a follow-up, not
via drift from this session.

## Mechanics notes

- Bump-exempt reading holds: nothing shipped changes tool behavior;
  both files are prose contract docs.
- Anchor stability is asserted mechanically: validation pins the
  pre-change heading-census sha256 for both files and the
  post-change census is byte-identical (no heading added, removed,
  or renumbered).
- The crafted validation epilogue emits its `reconcile_claims` call
  inline at the end of the pasted fragment; pasted before the
  checks per its own instruction, that call fires early. I removed
  the early call and kept the end-of-script one. Possibly worth a
  crafter tweak (emit the definitions and the call as separable
  fragments); flagging rather than proposing formally since it may
  be deliberate.

## Proposals

- **What:** True up BALE.md's own §7/§7.2 prose wherever it still
  describes includes as the gated scope, if session B's sweep does
  not already cover it.
  **Why:** This session's sweep was confined to its two-file
  forecast; I could not verify BALE.md (shipped read-only, session
  B's forecast) agrees with the revised TARBALL.md §3.4 rows that
  point into it.
  **Scope hints:** BALE.md §7.2 (`--read-only`, `--supersedes`
  semantics); only after B lands, to avoid restating what it
  already fixed.
