# notes.md — 2026-08-29-exchange-doctrine-002

Doc-only, as asked: no bin, schemas, or VERSION touched, no bump.
Every path in `changes[]` is inside the forecast. ADRs 0010–0012 are
byte-identical to the shipped copies (validation pins their hashes).

## Choices between two valid rewrites

- **TARBALL.md §2 heading.** Renamed "Three Exchanges" → "Four
  Exchanges". Nothing cites the old title by name (only by §2), so
  the number stays stable and the title stops lying. The alternative
  — keep "Three" and footnote the fourth row — read as the fork
  surviving in the heading.
- **BALE.md layout.** Took the §8.11 option *and* added a §5
  command-surface row. §5 is "the full target surface" with pending
  phases as forward-looking rows, so relay needs a row there
  regardless of where its contract lives; §8.11 sits beside §8.10.2
  in the same register. Phase column says `pending` rather than a
  version, since the sibling owns the bump.
- **BALE.md §8.11 step 2.** I first wrote a `from`-alternation refusal
  (a side may not post twice in a row) and took it back out — D4 does
  not say it, and a worker legitimately asking a follow-up round
  after an answer is a `from: worker` after a `from: planner`, so the
  rule was wrong anyway. What survives is only what D3/D4 imply:
  schema-valid, `session_id` = sid, `round` = next `NNN`. If you want
  a sequencing rule, it's the sibling's call.
- **BALE.md §11 row 34.** Written as a shape gate at "relay
  pre-flight" — a phase name that doesn't exist yet in the table.
  The alternative was to fold relay into row 25's non-normal-kind
  gate; I kept them separate because row 25 is apply-side and relay
  never runs apply's pipeline.
- **TARBALL.md §5.9.2 exchange-record prose.** Described the record
  in words (field names in backticks, no JSON block) so the section
  can't be read as a second schema home; D3's shape is repeated
  verbatim only in ADR-0017 and BALE.md §8.11, which are project-side
  and can cite the schema file by path.
- **PLANNER.md §15 and the escalation record.** D6 keeps the
  master→architect leg with the harness project; §15 now says the
  two records coexist and share `amendment_target`, and stays at that
  depth. The bullet on priority classes keeps the `batched` doctrine
  as written (D6's "non-blocking mid-work inquiry: not in this arc").
- **Retired-phrase list in `validation.sh`.** Twelve literal
  substrings, my selection from the passages I rewrote plus the two
  softening forms the brief forbids. Byte-exact, case-insensitive,
  across the four edited docs.

## Forks found in the sweep that were not on your list

All made role-only; each is in the diff and easy to revert if you
disagree.

- **TARBALL.md §3.4** — "doctrine for when an orchestrator exists,
  not a change to the human path, which needs the paste-ready
  command" (the rescope-offer consumer sentence). Now: the planner
  re-derives, the paste-ready form serves the courier, whoever holds
  either role. This is the exact phrase ADR-0011's Notes used, living
  in a second place.
- **TARBALL.md §5.4.1** — "The planner (the architect today, an
  orchestrator later)".
- **TARBALL.md §4.2, §4.3, §4.4** — "The architect pastes it… /
  audits this before pasting / returns the contents" → courier.
  Language only; the probe's mechanics, properties, and §6.5 are
  untouched (D6). §4.1's "which option the architect prefers" →
  planner (that one is intent).
- **TARBALL.md §5.1** — "the architect answers" → the planner
  answers through the thread.
- **PLANNER.md META** — the halves sentence called sections 8–19
  "the working doctrine for the harness era"; aligned with §8's
  narrowed line so the two don't disagree.
- **PLANNER.md §8's role paragraph** — "*Master* names the planning
  agent of the harness era" → "a planner that is itself a session".

Left alone, deliberately:

- **CLAUDE.md §6** "whoever runs pack and apply, today me" — role
  first, holder second; not a shape gate.
- **PLANNER.md §9** "foundational design principle of the harness
  era" and **§12/§16/§17** markers — genuinely about attention
  economics, sandboxing, refresh scheduling, and spend; that's the
  harness-era residue D1 leaves standing.
- **BALE.md §6.5** — unchanged per D6, though it still says "the user
  runs it, the user pastes output back". Say the word and it goes
  role-only in a follow-up; I did not want to touch a section the
  brief pinned.

## One out-of-brief edit inside a forecast file

**BALE.md §6.6** pointed the escalation doctrine at
`claude/context/orchestration.md` §8, which has been a tombstone
since 2026-08-16; the home is `PLANNER.md` §15. I re-pointed it while
adding the coexistence sentence to the same paragraph. The old
pointer wasn't wrong when written; it just never got swept. Flagged
here rather than shipped silently; revert the one clause if you'd
rather keep the diff to the arc.

## Validation notes

- The crafter's `--doc-assertions --index claude/INDEX.md` block
  fails on this repo independent of my change: `INDEX.md` sits under
  `claude/`, so its repo-root `BALE.md` entry resolves to
  `claude/BALE.md`, which does not exist. I replaced that block with
  a narrowed session-specific check (all `context/adr/` entries
  resolve; ADR-0017 listed) and kept the crafted ADR-guards block.
  See Proposals.
- The two unittest runs and the token/phrase checks were run on a
  staged replica built from the request's `context/` plus the mirror
  (`claim_basis: observed`); the remaining assertions are
  `predicted` — they read only files this response ships or pins.
- All 156 numbered headings across the four edited docs survive
  (asserted); all `DOC.md §N` cites resolve (`test_doc_crossrefs`).

## Proposals

- **What:** Make `INDEX.md`'s `BALE.md` entry resolvable to the
  crafted INDEX-coherence check — either an explicit `../BALE.md`
  path, or a documented exemption in the crafter's `--index` block
  for entries annotated "(repo root)".
  **Why:** As it stands, no bale-src session touching `claude/`
  docs can ship the DOCS.md §9 contract row as crafted without a
  guaranteed `[FAIL]`, which quietly pushes sessions toward
  hand-rolled INDEX checks (as this one did).
  **Scope hints:** `claude/INDEX.md` one line, or
  `tools/craft_response.py`'s index block; tiny.
- **What:** Role-only sweep of **BALE.md §6.5** and of the ADR-0010
  language quoted in **INDEX.md**'s 0010 entry ("the architect's
  environment"), once the code siblings land.
  **Why:** D6 pinned §6.5 for this session; the sweep is one
  sentence and belongs with the sibling that ships relay, so the
  design doc's probe and exchange sections read in one voice.
- **What:** `TARBALL.md` §5.9.3's tombstone could name BALE.md
  §8.10.2 *and* §8.11 generically ("the bale tool's design
  documentation" already covers both) — no change needed now; noting
  that the tombstone's "apply-time behavior" wording is slightly
  narrower than the thread it now points at.
  **Why:** Cheap to fold into whichever sibling next edits §5.9.
