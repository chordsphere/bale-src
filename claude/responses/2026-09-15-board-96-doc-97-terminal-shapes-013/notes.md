# notes.md — 2026-09-15-board-96-doc-97-terminal-shapes-013

Doc-only, bumpless, all eight sites landed. Nothing shipped outside
the write forecast; DOCS.md is in the forecast but unchanged, on
purpose (below). No sanctioned-pair extract moved, so
`test_sanctioned_pairs` ships untouched; `test_doc_crossrefs`
gains a pin class. No light block or clarification was needed —
the brief delegated every judgment I hit, so each is a named
assumption here rather than a round trip.

## Things I decided that you should ratify

**Sentinels.** `=== LIGHT BEGIN <sid> ===` / `=== LIGHT END <sid> ===`,
on the probe's `=== PROBE BEGIN <slug> ===` model as the brief said,
with the sid rather than a slug so the block names the session it
suspends (the exchange block also keys on sid). If the crafter's
render next wave wants a different token, §5.10 is the place to
change it — the sentinel is named exactly once there and once in
§10.4.

**Field labels.** The four labels are exactly the brief's — `[n]
question` / `while doing` / `would assume` / `why blocked` — and
§5.10 states the mapping onto `question`, `context`,
`default_assumption`, `why_blocked` in order, so the "one row feeds
either courier" claim is checkable against the schema.

**No integrity trailer on the light block.** The probe and exchange
blocks carry one because they are pasted machine output and a
truncated paste is a real failure. A light block is at most three
hand-written entries read by a person; a trailer would be ceremony.
Left out deliberately, not forgotten.

**"Formal" re-enters through §10.3.** §5.10 and §10.4 say a
"formal" reply has the worker re-emit the same rows as round one of
a clarification through the existing path. I did not invent a new
mechanism for it — the point of the shared row is that none is
needed.

**The §9 pivot bullet — the fifth site.** "Stops cleanly, notes
where it stopped in `notes.md`, and asks" reads as a prose ask to
me: the thing being asked is *which way now?*, and nothing in the
sentence made it a stop-and-wait. I pointed it at the shapes — a
light block if the redirect resolves in a word, a clarification
otherwise — and kept the rest of the bullet. If you read it as
stop-and-wait, reverting that one bullet is a two-line change and
nothing else depends on it.

## Sites beyond the brief's eight (all in TARBALL.md, all in forecast)

Grepping the applied docs for chat invitations turned up four more
phrasings that would have contradicted the §5.10 I was landing. I
rewrote them rather than ship a doc that argues with itself; each is
a small edit and none touches a pinned extract:

- **§4.1**, the conceptual-gap boundary bullet: "Quick, non-blocking
  questions resolve in chat" → the light block, admitted by count,
  with "Neither is a question asked as prose" appended.
- **§5.1**, the narrow-rule paragraph: "a conversational reply is
  the right response to a scope question, a concern, or a quick
  clarification" → the light block for a short non-blocking set,
  and "A concern or a scope observation that asks nothing is said
  in prose; an ask is never prose." The distinction I drew: prose
  that *asks* is what the ruling bans; prose that reports a concern
  still has a place.
- **§2**, the closing sentence after the exchanges table: kept
  "Chat carries conversation and never a blocking ask" and added
  that the one ask chat does carry is the light block, a shape
  whose trail is the eventual response.
- **INDEX read-paths**: a trigger row for the light block →
  §5.10, beside the clarification row. CLAUDE.md's INDEX gained
  the parallel row, and its §4 division-of-labor "Intent questions"
  cell now names the light block beside the exchange.

Also added, as a derived checklist: **§10.4 "Returning a light
question block instead"**, four steps, parallel to §10.2/§10.3. §10
is where a worker looks at session end and the light block is a
fourth ending; leaving it out felt like the doc's own harness
property ("every ending parses") having a hole. Cut it if you want
§10 to stay at three.

Phrases I left alone, deliberately: TARBALL.md META's and §8's
"pause and ask" when `TARBALL.md` itself is missing (a hand-rolled
request is outside bale's session model, and the crafter that
would emit a clarification may be missing too); CLAUDE.md §8's
"says so and asks" (it describes `notes.md` voice — that ask *is*
the flagged-assumption path); §9 "Pure questions — answer in chat"
(conversational mode); §11.6's "a sentence in chat" (a disclosure,
not an ask); and §5.9.1's breach fallback and §10.1 step 2's
warning, which are the ruling's own floor.

## The ADR spelling (row 97)

CLAUDE.md's INDEX row and TARBALL.md §3.1's example changed as the
brief specified. Two things to know:

1. **DOCS.md is unchanged, and the brief's condition did not
   fire.** Its location of record is `claude/context/adr/` (§1
   table, §4.4). It also says `context/adr/` (§2.2's INDEX.md
   example, §3.2) and bare `adr/` (§3.1's template text, §5 "Older
   ones live only in `adr/`"). I read those as relative shorthands
   for the same directory — the INDEX.md example is *defined* as
   relative to `claude/` — not a third location, so I changed
   nothing. If the desk wants the bare `adr/` in §5 spelled out
   too, that is a one-word change; it is listed under `deferred`.
2. **TARBALL.md §3.1's example now reads `context/` containing
   `context/adr/`.** That is the brief's literal instruction and it
   matches DOCS.md's INDEX-relative spelling, but under §3.1's own
   prefix rule ("`context/<p>` is the repo path `<p>`") a tree
   reader would resolve it to repo `context/adr/`, not
   `claude/context/adr/`. The same is already true of the
   `INDEX.md` and `STATE.md` lines above it — the example predates
   the prefix rule and is illustrative. I followed the brief;
   `claude/context/adr/` on that line would be the tree-literal
   spelling if you'd rather.

## Where to look on review

- **TARBALL.md §5.10** in full — it is core §5 (every-read), so its
  length matters. Five paragraphs plus one example; the two
  VERBATIM sentences are the second paragraph's first sentence and
  the fourth paragraph's second. The example is illustrative (Vue,
  per §1's convention) and every line is under 70 columns.
- **CLAUDE.md §3's shapes paragraph** — "four" became "five", and
  the every-turn sentence at its end is the opener's sentence with
  "you end in this session" → "Claude ends in tarball mode". The
  bailout stays outside the four-shape list in that sentence
  because a bailout *is* a response tarball (§11.4); the paragraph
  still lists it as a shape.
- **CLAUDE.md "When Claude is unsure which mode"** — three
  sentences now; the old "default lean: conversational" is gone
  because the opener answers the question the lean existed for.
- **PLANNER.md §15's new bullet** carries the three-replies
  sentence verbatim as well (validation asserts it in both docs) —
  deliberate cross-doc statement, one for each side of the
  exchange, not a new sanctioned pair: the doctrine's home is
  §5.10 and PLANNER.md names the packer's half.

## Validation

`validation.sh` runs the four doc-pin suites, then whitespace-
collapsed verbatim assertions on the three marked sentences (V2
in both TARBALL.md and PLANNER.md), heading placement (5.10 after
5.9.4 and before 7; 10.4 present), absence of seven struck phrases,
the ruling's floor sentences intact, the ADR spelling in all three
docs, and `bin/VERSION` at 0.4.32 (a `[SKIP]` if a sibling's bump
has landed in staging first — doc-only, no bump shipped). Run
against a staging copy here: 22 tests, every assertion `[PASS]`.
Claims are `observed`. The new `TerminalShapePins` were also run
against the *unmodified* docs and fail there on all eight subtests,
so the pins bite.

## Proposals

- **What:** a `--light` (or similar) render in `tools/craft_response.py`
  that emits the §5.10 block from a filled question row set, and the
  `feedback.self_reported` count the brief mentions.
  **Why:** §5.10 was written format-first so this is mechanization,
  not design; the sentinel and labels are fixed there. Already the
  crafter pair's next-wave work per the brief — noted so the shape
  in §5.10 is the one it renders.
- **What:** `tools/response_lint.py` could flag a `notes.md` that
  mentions "LIGHT BEGIN" without a matching answer line.
  **Why:** §5.10 says silence in `notes.md` about an emitted block
  is the tell of a lost answer; that is a cheap textual check the
  lint is positioned to make. Low priority.
