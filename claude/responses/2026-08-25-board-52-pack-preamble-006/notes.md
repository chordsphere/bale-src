# notes.md — 2026-08-25-board-52-pack-preamble-006

## What landed, in one breath

`session_opener_block()` in `bin/bale_pack.py` builds the paragraph;
the human report appends it as the final trailer lines (after the
read-only close-out, so it always ends the report), and the `--json`
path prints it after the JSON line. One report site serves all three
shapes — fully-specified, wizard, and read-only converge on the same
`cmd_pack` summary code, which is what makes "every pack shape" a
single edit. BALE.md §1 and §7.7 are re-pointed; §7.7 now carries the
opener's contract. New suite `tests/test_pack_opener.py` (5 tests);
full project suite run: 572 tests OK.

## The --json interplay (your call requested; here it is)

**Decision: the opener rides stderr; stdout stays exactly the one
JSON line.** Implementation is one `print()` after `emit_json_line` —
`enable_json_mode()` has already rebound `sys.stdout` to stderr, so
the block travels the same route as every other human-facing line
under json mode, and it still ends the run (nothing prints after it).

Why not a JSON key (or both): a structured `opener` key belongs in
`format_pack_json`, whose docstring in `bin/bale_report.py` owns the
stable key contract — and `bale_report.py` is a desk-ruled hot file
for this pair (the shared-rendering-helper lost-update hazard your
brief names). Rather than smuggle a key in by post-processing the
JSON string in pack (which would fork the contract's one home), the
key is proposed below and stderr carries the block today. A machine
consumer that wants the paragraph can rebuild it from `sid` + the
manifest's `goal` until the key lands; the human pasting from a
json-mode terminal sees the block exactly where the tree-position
banner already lives.

## Doctrine sweep (every swept line, enumerated)

Grepped BALE.md (the one doc in my forecast) for the hand-carried
opening-paragraph doctrine — `preamble`, `opening`, `by hand`,
`copy-paste`, `paste`, `upload`. BALE.md never specified the
paragraph itself (it lived only in your hands), so the sweep found
delivery-flow lines rather than wording doctrine:

1. **§7.7 Output** — "The user copy-pastes or uploads from there."
   → re-pointed: the user uploads the tarball and opens the chat with
   the emitted opener; "the opening paragraph is bale-emitted, not
   hand-carried." The new **The session opener** block follows it as
   the contract's doc home.
2. **§1 step 1 (Pack)** — "Hand the tarball to Claude (via
   copy-paste, upload, whatever)." → re-pointed at the §7.7 opener:
   "the opening paragraph is emitted, not typed."

No other BALE.md line described the hand-carried paragraph. Doc lines
outside my forecast that brush against it are in Proposals, not
edited.

## Out-of-forecast path (admit at apply)

- **`tests/test_pack_opener.py`** (created) — the brief's sanctioned
  new-suite path. The goal needed its own pinned behaviors
  (end-position, identity carriage, per-shape, --json streams), and a
  dedicated suite matches the tests/ directory's
  one-feature-per-suite pattern. The forecast's
  `tests/test_tree_position_echo.py` turned out to need **no edit**:
  its pins (banner-before-summary, one-line json stdout, sid
  non-leakage) all still hold with the opener appended — verified by
  running it, not by assuming — so I left it byte-untouched rather
  than growing an unrelated docstring's scope. An unused forecast
  entry is the ask overshooting, which the brief itself anticipated.

## Staleness caveat, confirmed

Board 50's changes to `bale_pack.py` did move things, and your
stable-phrase citation held: the trailer block whose lines read "Send
the tarball to Claude" / "run: bale apply <response-tarball>" matched
at exactly one site in the applied tree (`cmd_pack`'s summary
emission). Unambiguous-phrase-match won; no line-number archaeology
needed. I kept that trailer's wording untouched — it is the report's
next-step hint (and other suites' locator), distinct from the opener,
which follows it.

## Wording choices (yours to ratify — bale owns the paragraph now)

The first line ("I'm using \"bale\", a CLI that packaged the attached
request tarball.") deliberately echoes the opener you've been typing
by hand, so the fresh session's footing doesn't change with the
ownership. The sid rides inline; the goal rides one never-wrapped
line prefixed "Goal, verbatim from the request manifest: " —
`format_summary_block` never wraps trailer lines, which is what keeps
substring checks on the goal honest. The read-only identity splits
over two lines to keep the sid line short. Scissor lines are the copy
frame; the test suite restates them as literals so a silent rewording
breaks a test.

## Proposals

- **What:** Add the opener as a structured `opener` key (string, the
  full paragraph) to `format_pack_json`, beside the existing additive
  keys. **Why:** json-mode consumers currently must rebuild the
  paragraph or scrape stderr; the key contract's one home is
  `format_pack_json`'s docstring, which this session couldn't touch
  (hot-file ruling on `bale_report.py`). **Scope hints:**
  `bin/bale_report.py`, `tests/test_pack_opener.py`; only after the
  board-51/52 pair lands.
- **What:** Emit the opener on `bale handoff`'s report too — its
  trailer twin lives in `bin/bale` (the handoff summary site).
  **Why:** a handoff opens a session exactly like pack does; its
  successor is also a chat message, so the
  every-command-names-its-successor argument applies verbatim.
  **Scope hints:** `bin/bale` — claimed by board 51's forecast this
  sitting, so proposed rather than shipped; reuse
  `session_opener_block` (already importable from `bale_pack`).
- **What:** The shared version bump for the board-51/52 pair, plus
  tagging BALE.md §7.7's "(board 52)" label with the landed version
  number. **Why:** `bin/VERSION` is desk-landed after both apply
  (hot-file ruling); the §7.7 block cites the board because the
  version didn't exist at build time. **Scope hints:** `bin/VERSION`,
  one-line BALE.md touch-up; desk-side.
- **What:** A one-line pointer in `docs/CLAUDE.md` §3's "When the
  chat preamble and the manifest goal disagree" noting the preamble
  is now bale-emitted with the sid and goal from the manifest — so
  preamble/manifest drift shrinks to the stale-paste case. **Why:**
  that doctrine was written for the hand-typed preamble era; the
  emitted opener changes its main failure mode. **Scope hints:**
  global docs, outside this forecast; a docs session against
  bale-src.
