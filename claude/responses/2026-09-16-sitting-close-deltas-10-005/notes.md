# notes — 2026-09-16-sitting-close-deltas-10-005

One file, `claude/MASTER.md`, bumpless, insertions only. Blocks A–F
landed verbatim at their anchors; every anchor was unique where the
brief quoted it. No light block or clarification — nothing in the
brief was a blocking gap, and every disagreement below is the kind
the brief says to land as written and name here.

## The edits that are not verbatim text

- **The sid fill.** Block A's "`2026-09-16-sitting-close-deltas-10-<nnn>`
  (fill from your sid):" became "`2026-09-16-sitting-close-deltas-10-005`:",
  matching close-9's "close recorded by `<sid>`:" shape. The
  parenthetical was an instruction, not text, so it went with the
  placeholder.
- **Blank lines between new numbered items.** Rows 104–106 and
  evidence entries 141–146 arrived as one run with no separators; the
  board and §6 separate every numbered item with a blank line, so I
  added them. Whitespace-only, invisible to a collapsed compare.
- **Hand-wrapped inline text.** The eleven registry brackets and the
  ruling-queue entry were given inline, so I wrapped them at 70
  columns with the list's two-space indent. The ruling-queue entry
  lands as a plain bullet (the brief's text has no bold title, unlike
  the one existing entry).
- **Bullet spacing.** The brief cites "DOCS.md's rule"; the DOCS.md in
  this request has no bullet-spacing rule, so I followed the file's
  own convention (tight bullets inside a block, a blank line before
  and after each close block). `grep -c 'continue-plan-009 sitting'`
  over §3 is 1; over the whole file it is also 1.

## Where a block disagrees with its sources (landed as written)

1. **Row 97's bracket, first sentence.** It says TARBALL.md §3.1's
   example reads `claude/context/adr/`. It reads `context/adr/` — the
   TARBALL.md in this very request, the `context/` example tree, and
   96-doc's notes (item 2: "now reads `context/` containing
   `context/adr/`") agree. The bracket's last sentence ("§3.1's
   example is illustrative under the prefix rule; left") is right; the
   first sentence overstates it. CLAUDE.md's INDEX row does say
   `claude/context/adr/`.
2. **Block A's fixture-defect bullet cites "§6 entry 143".** The
   fixture-defect entry is 142 ("Absence is not a drop"); 143 is the
   target-base validation invariant. Looks like an off-by-one.
3. **Row 99 says 99b now carries "open's order"; row 68 says the
   BALE.md open-order sentence landed at 47a.** 47a's notes confirm
   68's version: the `bale open` sentence went into the §5 row word
   for word, and an own-words version into §6.7. 99a's Proposal 2
   asked for it before 47a had merged. The new 99b registry entry
   (Block C) correctly leaves it out, so only row 99's list is stale
   — or 99b's item is verify-only, which the row doesn't say.
4. **Row 106 says "five riders on one file".** 102's Proposal scopes
   `fail_not_found` to `bin/bale` plus `bin/bale_apply.py`'s call site
   and `ExplicitNameMissTest`; pack-UX's `from_lines` split names pins
   in `tests/test_pack_guards.py`. The row's own parenthetical says
   `bin/`, so the forecast is probably still right, but "one file" is
   not.
5. **Row 82: "the four lint-owned members seeded `false`".** Per
   91-82's notes, `response_kind` is filled from `--kind`; the four
   `false` placeholders are `schema_valid`, both `mirror_agreement`
   directions, and `claims_subset`. Four values, not four members.
6. **Row 47 vs row 106 on agreement.** Row 47 says the card and amend
   "agree by construction"; row 106 queues making them "agree
   structurally, not by test". Both are true of different pairs in
   47a's notes (the card's successors come from the stamp outcome;
   `compose_retry_successor` in `bin/bale` is a mirror pinned by
   `HoldCardAgreementTest`), but side by side they read as a
   contradiction.

## Claims I could not check against the included notes

Not disagreements — the notes are silent, so these rest on the desk's
ledger: 47a consuming the `validation_will_run`/`corrects` rider (row
47 and its Block C bracket); 47a widening BALE.md's 102 sentence to
name handoff (102's notes left that to the desk); 96-crafter
retiring the lint docstrings' hand-added `provenance` line (row 69 —
that was 91-82's Proposal 2, and 96-crafter's notes don't mention
it); the pack-json `sweep`/`include_group` key "named and deferred at
47a"; the picker's "sha prefix" and "typed number"; row 84's "stdlib
names never fire"; "all four applied clean on the first attempt";
the 0.4.32 provenance stamp at the open. Everything else I checked
matched: sids, versions, the 5/5 and two-of-eight HOLDs, v2
`cc6b44200d8d`, the 49 bare-sibling files, the three answers "as
assumed" and the one "no", 96-crafter's omitted counts.

Two smaller things. The "last section-29 string literal" bracket
records the renames too, but the separate "The two `_section_29`
test-id renames" registry entry stays unbracketed — the brief didn't
ask, so I didn't. And evidence 145's "100 KB / 75 KB tools" are
presumably from the transcript's pack; this request ships
`craft_response.py` at 154 KB and `response_lint.py` at 80 KB, and
the five docs at almost exactly 250 KB.

## Look closely on review

- **Block D's heading.** The two contracts land after the re-attempt
  contract, inside "New, ratified 2026-09-15 (the continue-plan-004
  sitting…)". Each entry says "Ratified 2026-09-16", but the heading
  above them dates them to the previous sitting.
- **Wave 3's "all beside each other".** See Proposals.

## Validation

`validation.sh` asserts each block with whitespace collapsed *and* at
its position: A as the last content of §3 directly after close-9;
each of the thirteen growths as its row's last content; 104–106 as
the board's end; the ruling entry inside the ruling queue; each
bracket as its registry entry's last content and the seven new
entries as the list's end; D directly after the re-attempt contract;
E as §6's end; F directly after the registry-riders line; the §3 count
of one with no placeholder left. A ninth check proves insertions
only, diffing against `git show HEAD:claude/MASTER.md` when that copy
hashes to the request's base sha, and SKIPs with the reason
otherwise. Rehearsed on four trees: changed (exit 0, 9/9), base
(exit 1, eight FAIL), a mutation dropping one bracket line and
editing one base line (exit 1, exactly those two checks FAIL), and no
git (exit 0, the ninth SKIPs). Claims are `observed`.

## Proposals

- **What:** re-check wave 3's forecasts before emitting it. **Why:**
  the stats micro carries the dossier wiring, whose registry entry
  scopes it to `bin/bale` (the stats subcommand's argparse and
  dispatch), and row 106 holds `bin/bale` — the gate will refuse the
  second of the two. Separately, 106's `fail_not_found` rider touches
  `bin/bale_apply.py`'s call site, and 47b's
  `format_walkthrough_summary` rider touches `bin/bale_apply.py`'s
  HOLD log line. **Scope hints:** the sequencing line in this close
  block; either 106 takes the dossier wiring or one of each pair
  serializes.
- **What:** a "New, ratified 2026-09-16 (…)" heading line above the
  two new §5 contracts. **Why:** they currently read as 09-15 rulings
  (see above). **Scope hints:** one line in §5, next MASTER.md touch;
  the §3 phrase count is unaffected.
