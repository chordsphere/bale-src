# Notes — 2026-09-17-guard-maintenance-006

All four ratified items landed. Every `changes[]` path is inside the write
forecast, so there are no out-of-forecast paths to admit. Bumpless relative
to this response: no `bin/VERSION` change, no version tag added or removed,
no changelog record touched.

## Light question block (one, answered "as assumed")

1. *Should the hyphenated board row also sit in the schema group's deny
   table?* **Yes (as assumed).** Both tables hold the same compiled object,
   `BOARD_HYPHEN_PATTERN`, and a test pins that. I treat it as the schema
   table's existing ratified board row widened by one hyphen. The other
   rows stay per-surface, and the docstring says this.
2. *Should an undated kebab fragment like `fx-board-12` be caught?*
   **Yes (as assumed).** Only a token carrying a `YYYY-MM-DD-` date counts
   as a sid. The rest is a citation.
3. *What happens to the other provenance leftovers in `tools/craft_response.py`?*
   **Proposed, not rewritten (as assumed).** See Proposals.

## The anchor design (item 2), for review

The pattern is
`(?<![\w-])(?:(?!\d{4}-\d{2}-\d{2}-)\w+-)*board(?:-row)?-\d`.

How it decides:

- A match must begin a kebab token, meaning no word character or hyphen
  directly before it.
- Every hyphen-separated segment it walks through before `board` must not
  begin a date.

Why I didn't use a fixed-width lookbehind `(?<!\d{4}-\d{2}-\d{2}-)`, which
is the brief's literal wording: it only tolerates sids where `board` is the
first slug word. It would flag `2026-09-17-fx-board-12-cleanup-003` and
`response-<sid>.tar.gz`. The token-based anchor tolerates both and still
catches:

- a bare `board-13c`
- a parenthesised `(board-13c)`
- `board-row-54`
- a path-prefixed `claude/board-7`
- a `board-13c` that sits beside a sid on the same line

It still ignores `keyboard-1`, `onboard-3` and `billboard-9`. No
pathological backtracking: a 10,000-character kebab run takes about 1 ms.

One known blind spot, written into the docstring: a sid hard-wrapped at the
hyphen just before `board` shows up to the line scan as a bare
`board-<digits>`, so the guard fails it. That errs on the loud side.

Evidence, both directions:

- Against the **original** tools, the guard fails on exactly
  `tools/craft_response.py` line 2032 and passes the live sid at line 1516.
- Against the staged tree, all 11 guard tests pass.

## Item 3: what "byte-identical in effect" rests on

`validation.sh` checks three things on each tool:

- **AST fingerprint.** It hashes the AST with docstrings stripped (comments
  are never in the AST) and compares against a fingerprint computed from
  the request's base files. Any change to code, constants, embedded schemas
  or emitted strings would move it.
- **Line counts.** Still 3259 and 1771, so the crafter's `(~line N)` table
  of contents stays true.
- **No leftover strings.** Neither old phrase remains.

Outside `validation.sh`, I also confirmed that both tools' `--help` output
matches the base byte for byte.

The response_lint rewrite also fixes that comment's overlong line, and the
new text still fits in the same two lines.

## Item 4: the pin

`CurrentVersionRecordTest` reads `bin/VERSION` and checks that
`claude/changelog/<version>.json` exists, validates, and carries that
version. It uses a small helper, `version_record_problems`, so the failure
direction can be tested without touching the corpus:

- A version with no record fails, naming the path to write.
- Wrong-version, invalid and non-JSON records each fail, naming their path.
  These cases are built in a temp directory. The module docstring's
  "nothing is written" line now says "nothing is written *to the repo*".

Rehearsal: bumping staging's `bin/VERSION` to 0.4.36 without a record fails
loudly with `claude/changelog/0.4.36.json is missing`.

This pin binds whichever session bumps next. If 106 bumps
`bin/VERSION`, it has to ship the record in the same response.

## Claims

`tests: test_craft_response` is claimed `pass` with basis **predicted**,
not observed. In my sandbox, 158 of its 160 cases pass (16 of them
slow-gated skips). The other two are `PackInjectionSurface` cases, and they
fail identically on the untouched request tree. The reason: they exec
`bin/bale_pack.py`, which this request did not ship (106 holds it). Your
staging copy has the file, so I expect them to pass there. If they fail,
check what 106 has done to `bin/bale_pack.py` before suspecting this
response, since nothing here touches the injection surface. Every other
claim was observed in a rehearsed staging run: modes stripped on overlay,
`apply.sh` run, manifest placed at `.bale-manifest.json`.

## Proposals

- **What:** Restate the three remaining provenance leftovers in
  `tools/craft_response.py` self-standingly:
  - lines 108 and 359: "registry fold-in, ratified 2026-08-18"
  - line 544: "fold-in: 008's accepted proposal"

  **Why:** They are the same class as the two this session removed.
  Project-side provenance means nothing in other projects. No guard shape
  catches them (no board or evidence number), which is how they survived.
  **Scope hints:** comment and docstring text only, one line for one line,
  verified the same way as here (AST fingerprint plus line count). Could
  pair with any future crafter session.
- **What:** Decide whether `fold-in: <NNN>'s accepted proposal`-style
  session-number citations deserve a deny shape.
  **Why:** Line 544 shows that a bare session number is a citation form
  the tables don't cover. A shape would need care, because
  `request-006`-style directory names are legitimate.
  **Scope hints:** `tests/test_global_doc_selfcontainment.py` only. Worth a
  specimen survey of the scanned surfaces first.
