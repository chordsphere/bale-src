# notes — 2026-09-17-board-69-selfcontainment-fix-both-005

Small one, as advertised. The brief's five sites were exactly the five
the guard flags on the shipped tip — I re-grepped both tools for every
deny shape (board/row digits, evidence digits, the four literals, the
wrapped pointer phrase) before building, and nothing else turned up.

## What the rewrites say

- `tools/response_lint.py` 52, 57 — the `claims-value` and
  `docs-read-stub` registry rows just lose `(board 69)`; the rest of
  each row already states the rule and its reason.
- `tools/response_lint.py` 1294 — `check_docs_read_stub`'s summary line
  now says what the warning most likely means (the crafter's stub,
  shipped unfilled) instead of where the ruling came from. The body
  below it already carries the why.
- `tools/craft_response.py` 632–634 — "board 69's registry rider"
  becomes the reason the scan accepts literal strings: rejecting them
  would report a working, hand-edited key as unset. Reflowed over the
  same three lines.
- `tools/craft_response.py` 1838–1839 — the parenthetical
  `(board 69, from 2026-09-01-board-70-doc-reachability-007's Proposals)`
  went in full. The guard tolerates the sid string, but the brief bars
  session references in the rewritten comments, and it was the same
  provenance clause. The replacement says the optional-key exception is
  deliberate; the following lines already give the reason.

Every rewrite keeps its file's line count, so the crafter's
`(~line N)` section TOC stays true. `validation.sh` proves the
comment-only claim rather than asserting it: it reverses the five
rewrites on the staged bytes, requires the result to hash to the
request's `base_files` stamps, and compares the non-docstring AST.
Neither tool reads `__doc__`, so docstring text cannot reach behaviour.

## Decisions to ratify

- **`corrects` is set** to `2026-09-17-board-69-selfcontainment-fix-004`.
  I read this as PLANNER.md §14's correctable-HOLD path (repack,
  `corrects:` preserving lineage). The retry verb is the brief's.
- **"Bumpless-under"** isn't defined in the five global docs. I read it
  as: no version bump ships, and the highest v-tag the touched files
  cite stays at or under `bin/VERSION` (the `scripts/build.sh`
  drift rule). Relative to this response: it adds and removes no
  version tag; both tools top out at `v0.4.34`, equal to the request's
  `bale_version`. `validation.sh` checks this against staging's
  `bin/VERSION`, and SKIPs with a reason if that file isn't there.
  Correct me if the term means something narrower.

## Claim bases

`tests/test_craft_response.py` is claimed `pass` but only *predicted*.
In my sandbox (no `bin/`), 158 of its 160 tests pass and 17 skip for
missing `bin/`. The other two, `PackInjectionSurface`, fail with
`FileNotFoundError: bin/bale_pack.py`. Base bytes fail the same two in
the same way, so this change didn't cause them. In staging `bin/`
exists. The guard, lint, and schema-embed suites were observed passing
on the applied tree, and the guard was observed failing on base (2
failures: the board shape in each tool).

## Proposals

- **What:** a later pass over the tolerated leftovers in the injected
  tools: `craft_response.py` 2032's `fold-in: board-13c via the
  registry`, and `response_lint.py` 1324's "a planner ruling at the
  clarification round that shaped this check".
  **Why:** neither trips the guard (hyphenated `board-13c` escapes
  `\bboard \d`; "planner ruling" is no deny shape). Both are the same
  provenance-not-lesson idiom this session removed. `board-13c` in
  particular is a board citation that differs only by the hyphen.
  **Scope hints:** `tools/` only; if the guard is to catch the
  hyphenated form, that test needs a sid-aware anchor so it doesn't
  flag sid strings like 1516's. That edit is a deny-table decision for a
  sitting, not a worker's.
