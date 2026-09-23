# Notes — 2026-09-23-board-100-w1-doc-sweep-002

W1 of the 100 arc, the doc sweep. Everything the brief pinned landed;
the checkpoint's outcome list is reproduced by `validation.sh`'s
session assertions, which fail on the 0.4.41 tree (33 failures) and
pass on this one. The full unit suite is green on both trees (1468
tests, 48 skipped on 0.4.41; 1474 with the new guard's six).

## The rulings, as ratified

Each of these was ratified "as assumed" in the design sitting's three
light blocks (`2026-09-23-board-100-design-001`, revB); the trail is
that sitting's close notes. I list them here only to say where each
landed.

1. **The noun.** "the agent" everywhere a sentence is role-neutral;
   "the worker" / "the planner" where a sentence means one hat; "I/me"
   untouched. `grep -w Claude` is zero across the five globals and
   `README.md`. `CLAUDE.md`, `claude.ai`, `claude-decides`, `claude/`
   are not word matches and were not touched, per Amendment C.
2. **Depth.** Prose only. The file stays `CLAUDE.md` and every doc
   still cites it by that name; `docs/AGENT.md` does not exist.
3. **Compatibility.** No sentence in the six files promises a
   compatibility window; none did before, and I added none.
4. **The three inputs.**
   - `model_identity`: TARBALL.md §5.2.2's `mechanical` bullet now
     states the `<vendor>:<model>` form — lowercase, spaces to hyphens,
     `unknown` as the model token, no suffix — and says the schema pins
     the same form as a pattern (W2's regex). The pointer to which
     surfaces show the string goes to CLAUDE.md §11.7.
   - `includes_missing`: the same section names both entry forms — a
     path for a file, or a line opening `decision:` for a ruling the
     packer made but never transported.
   - `linkage.depends_on`: the schema's sentence lands in §5.2.2 whole
     ("null for a paste-back probe or an in-chat ask, which resolve
     within the session"), wrapped at the doc's column; the
     assertion compares it whitespace-collapsed.
   - "Validate before apply, always": both sites carry the rewording —
     land only through `bale apply`, which validates and stages before
     it merges; never hand-apply a tarball or bypass a HOLD. TARBALL.md
     §8's row keeps its `operator discipline` type and enforcement
     cell; CLAUDE.md §6's operator-discipline sentence keeps "tarballs
     are immutable once delivered" after it.
   - Light-block trail: PLANNER.md §6 gains a bullet, "A sitting closes
     with a light-block ledger" — the count, and each block's
     disposition (answered / as-assumed / formal / unanswered) — stated
     as a close-notes convention, not a record field, with the reason
     (bale never sees a block; a read-only session returns no
     response). PLANNER.md named the light block on one wrapped line
     before; it names it on several now.
5. **Surface notes.** CLAUDE.md §11.1 keeps its four bullets,
   surface-agnostic: the `claude.ai web/app` literal is gone from the
   compaction bullet (it now points at §11.7 for which surfaces
   auto-compact), and the tool-use-limit bullet says the paused loop
   resumes with full context and points at the table for how. §11.3's
   tool-use-limit non-trigger stays and cites the table. The new
   `### 11.7 Surface notes` sits past the core banner, after §11.6: one
   paragraph, then a table keyed by surface with one row, claude.ai
   (web and app), stating what happens at the window's edge
   (auto-compaction, not a hard error), how a paused tool loop resumes
   (press Continue; full context intact), and that the model picker
   shows the model string. Both banners now read §11.3–§11.7, and so
   do the reading-order item and the Every-session row that name the
   core span. I also added an INDEX read-paths row for §11.7 (filling
   `model_identity`, or unsure what the surface does at the edge) —
   the past-the-core rule says a subsection is read only when its
   trigger row fires, so it needed a row; the brief named the banner
   and the table, not the row. Strike it if you'd rather the table be
   reached only from §11.1/§11.3's pointers.
6. **Row 77.** Every lowercase inject form is gone from the six files;
   the docs say bale *carries* or *ships* the globals and the tools
   (`shipped by bale` in the §3.1 tree listing, `bale-carried` in
   §10.1, `carry-model question` in PLANNER.md's banner). The one
   surviving spelling is the identifier `INJECTED_TOOLS` at TARBALL.md
   §3.1, verbatim, on a line whose prose half ("also carried by bale,
   from the install") did change.

## Where "the agent" read wrong and I chose a hat noun

All in TARBALL.md, all "the worker", all sentences about the party
that builds a response tarball — the doc already used "the worker"
in the sentences around them, and "the agent" beside "the planner"
in §5.3's claims table read as if a planner might file claims:

- §5.1: the `validation.sh` comment in the shape block ("the worker's
  hypothesis test") and "If the worker touches `src/components/Foo.vue`".
- §5.1.1: "The responsibility sits on the worker"; "The worker does
  not use `apply.sh` to install dependencies".
- §5.2: the `deferred`, `claims`, and `"bailout"` bullets.
- §5.3: all of it, including the four-row claims table and the
  `unknown` closing sentence.
- §5.4: the notes.md bullets (decisions the worker made, anything
  surprising the worker found, what the worker would need to predict).
- §5.8: `context_loaded[].verdict` ("the worker can't measure
  token-spend").
- §7 lead and §7.2: the hypothesis-test sentences and item 6.
- §3.1: "Everything else the user wants the worker to see".
- §3.2: the `constraints`, `out_of_scope`, `expects_probe`, and
  `context_included` bullets.
- §3.4: the two rescope-offer sentences ("the one the worker emits",
  "as the worker would emit it").
- §4.2: "The block the worker returns".

Kept role-neutral on purpose: TARBALL.md META and §1; the bailout,
handoff, and diagnostics prose in §5.6–§5.8 (a planner session can
bail too, and "the next agent" is the handoff's reader whatever hat
it wears); all of CLAUDE.md, DOCS.md, CODE.md, and PLANNER.md, where
the sentences are about the session as such. Two grammar rewrites
beyond the noun swap: CLAUDE.md §1's friction sentence ("it is asking
me to absorb friction it was supposed to handle") and §4's closing
("fix something it could have included"), to avoid "the agent … the
agent … the agent" in one sentence. CODE.md's §7 heading is "Working
on Code the Agent Didn't Author" (title case). TARBALL.md §5.8's
"Claude-detected triggers" became "agent-detected".

One sentence was rewritten rather than swapped: TARBALL.md §1's roles
bullet said the old noun and "worker" read as the same party in
worker-facing prose. It now states the noun rule itself — "the agent"
is the role-neutral noun for the session these docs address,
whichever hat it wears; a hat noun where a sentence means one hat;
and in worker-facing prose "the agent" and "the worker" read as the
same party. That is the one place the docs explain their own
vocabulary, so it seemed the right place to engrave the ruling.

## Copied text a test pins by bytes — touched

- DOCS.md §9's closing and CODE.md §10's closing are a sanctioned
  pair pinned in `tests/test_sanctioned_pairs.py`; both sentences
  now open "The agent should surface…" / "The agent surfaces…" and
  the two extracts moved with them, in the same response, per the
  pair contract.
- `tests/test_doc_crossrefs.py`'s STRUCK_PHRASES pinned the absent
  chat invitation "Claude asks, in one sentence" in CLAUDE.md. Left as
  it was, the pin would have gone vacuous under the new vocabulary
  (the old spelling can never return while the guard holds), so it
  now pins "the agent asks, in one sentence" — the spelling a
  returning invitation would have to use.
- Nothing else pinned by bytes carried the noun: DOC_ASK_SENTENCE,
  DOC_DELIVERABLE_SENTENCE, the light-tier sentences, the relay
  paragraph (whose wrap the self-test anchors — I did not reflow it),
  and the byte-discipline sentences are all noun-free and untouched.
- The docstrings of both suites still say "Claude" in their history
  paragraphs (e.g. `"the worker" for "Claude"` at line 57 of
  test_doc_crossrefs.py); the guard scans the docs and README, not
  the tests, and rewriting history in a docstring would misstate what
  the earlier sessions wrote.

## Enumerated drift (TARBALL.md §5.4)

- `tests/test_global_doc_noun.py` — **created**, outside the forecast.
  The brief made the guard my call and said it lands as enumerated
  drift under `tests/`. It is a denied-token scan on the
  self-containment guard's model: two anchored patterns
  (`\bClaude\b`; `\binject(?:s|ed|ion|ing)?\b`, case-sensitive so
  `INJECTED_TOOLS` stays legal) over the five globals plus
  `README.md`, line-numbered failures, presence test, and a
  both-directions specimen class (`DenyShapeTest`) so a clean tree
  cannot pass vacuously. Run against the 0.4.41 tree it fails all
  twelve file×shape cells and its listing reproduces the brief's
  occurrence counts exactly. It is a separate file, not a fourth deny
  table in `test_global_doc_selfcontainment.py`, because that file
  is W3's. Also declared as `forecast_departures` in the manifest.
  Admit it at apply.

## Other observations

- The request's `context/bin/__pycache__/` shipped six `.pyc` files.
  Not mine and not in `changes[]`; mentioning it because a pack that
  ships bytecode is the kind of thing `.baleignore` usually filters.
- `validation.sh` uses `ast.parse` for the Python syntax check rather
  than `py_compile`, which writes a `.pyc` even under `-B` — I found
  that out by running the script in a staged copy. The full suite is
  gated behind `--slow` (it runs ~5 minutes against §7.6's 2-minute
  target); the four doc suites run unconditionally. Both ran here;
  the claims say `observed`.
- No line of the six files crosses 72 columns that did not already,
  apart from table rows and code blocks; a handful of paragraphs the
  sweep lengthened were rewrapped by hand.

## Proposals

- **What:** when W3 re-cites `INJECTED_TOOLS` and renames the file,
  fold the noun guard's presence test and SCANNED_FILES into the same
  motion (the guard names `docs/CLAUDE.md`), and consider adding a
  third deny row for the retired file name once `AGENT.md` is the
  only spelling.
  **Why:** the guard pins vocabulary the rename will change again;
  W3 is the session with both files in scope.
  **Scope hints:** `tests/test_global_doc_noun.py`,
  `tests/test_global_doc_selfcontainment.py`; only after W2 and W3
  land.
