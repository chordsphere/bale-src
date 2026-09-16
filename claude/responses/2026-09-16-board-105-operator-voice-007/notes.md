# notes — 2026-09-16-board-105-operator-voice-007

All five paths are inside the forecast; nothing ships outside it. No
probe, no light block, no clarification this session.

## What landed, and where to look

- **Opener** (`bin/bale_pack.py`). `OPENER_AUTHORITY_SENTENCE` and
  `OPENER_TOOLS_SENTENCE` sit directly under the grown
  `OPENER_SHAPE_SENTENCE`. The emitted lines are wrapped exactly as the
  brief's rendered block shows; both pack shapes get them through the
  shared return list, so there was no second site to edit. The em dash
  is a literal U+2014 in both the constant and the emitted line. My
  first edit wrote it as a `\u2014` escape (runtime-identical); I
  replaced it with the literal to match the rest of the file.
- **CLAUDE.md META**: the precedence sentence is replaced whole, bold
  kept on "this file wins", with the terminal period moving outside the
  bold since the sentence now continues.
- **CLAUDE.md §3 / TARBALL.md §5.10**: the second half is appended with
  the smallest rewrap that fits. In §5.10 that leaves "The light tier"
  ending a short line, so the rest of the paragraph does not reflow.
  The admission and three-replies sentences are untouched, and
  validation pins them as raw wrapped bytes, which is stricter than the
  suite's collapsed compare.
- **Registry rider (consumed)**: the INDEX light-tier row now reads
  "rendered by `tools/craft_response.py --light-block`, or authored by
  hand per `TARBALL.md` §5.10 where the crafter is unreachable". The
  fallback clause borrows §5.10's own phrase, so the two docs describe
  the fallback the same way. The row keeps its `TARBALL.md` §5.10
  pointer, and the crossref scan still resolves it.

## Untouched by design (not drift)

The four sibling precedence sentences (TARBALL.md, DOCS.md, CODE.md,
PLANNER.md META) still read "…from a prior session, **this file
wins.**". They are out of scope and ride the doc-injection sweep.
Validation asserts that TARBALL.md's twin is still in its old form, so
it can't be touched by accident while §5.10 was open. After this lands,
CLAUDE.md says "prior bale session" and the twins say "prior session".
That split is the known interim state.

## Judgment calls to ratify

1. **Literals beside constants, not derived lines.** I kept the
   existing pattern: the module constants and hand-wrapped emitted
   literals. Nothing at runtime reads `OPENER_*_SENTENCE`; only the
   pins keep the two in sync. Validation now also renders the block
   in-process and compares it against the constants for both shapes,
   so drift fails without needing a pack run. See Proposals.
2. **Shape sentence on the read-only shape too.** The brief asks for
   the authority and tools pins on both shapes. The existing shape
   test only runs the scoped pack. The new read-only test also asserts
   that the block closes with the whole shape sentence, so the second
   half is pinned on both shapes.
3. **Clean failure, not error.** `OpenerOperatorVoiceTest` returns
   after its subtests fail, instead of letting `.index()` raise. I ran
   the new pins against the unmodified tree: 6 clean failures, 0
   errors.
4. **Tools claim tested, not just asserted.** The opener now makes a
   factual claim about two shipped files. Validation AST-walks both and
   fails on any non-stdlib or network-capable import, or on a dynamic
   `__import__`. Today they import only `argparse, collections,
   datetime, gzip, hashlib, io, json, pathlib, re, sys, tarfile,
   __future__`.
5. **Bumpless-under** is stated relative to the response: validation
   reads the staged `.bale-manifest.json` and checks that no
   `bin/VERSION` entry is declared and every path is in the forecast.
   It does not compare a version literal.

## Validation notes

Claims are `observed`. I ran `validation.sh` in a scratch staging copy
(request `context/` tree, then `files/` overlaid, then `apply.sh`, then
the manifest at `.bale-manifest.json`), and all twelve checks passed.
The first run caught a bug in my own §5.10 check: its slice began at the
heading title, so the "first paragraph" was the title. The fix anchors
past the heading line. I then re-ran the checks against the unmodified
tree. The opener, doc, and rider checks fail there, as they should.

`test_pack_opener` needs a real `git`. It prints `[SKIP]` with that
reason if git is absent.

## Proposals

- **What:** add a unit test that calls `session_opener_block` in
  process and asserts that its collapsed block contains
  `OPENER_AUTHORITY_SENTENCE`, `OPENER_TOOLS_SENTENCE`, and
  `OPENER_SHAPE_SENTENCE` by reference to the module constants.
  **Why:** today the constants are dead at runtime, and the only link
  between a constant and its emitted wording is a restated literal in
  the test file. Three copies are kept in sync by hand, and the suite
  needs a full hermetic pack to check them. **Scope hints:**
  `tests/test_pack_opener.py`, and the next `bin/bale_pack.py` touch
  could derive the emitted lines from the constants.
- **What:** give the opener's tools claim a standing pin: a suite-level
  version of this session's AST import check over
  `tools/craft_response.py` and `tools/response_lint.py`. **Why:** the
  sentence "stdlib-only formatters with no network access" is now
  operator-voiced text in every opener. A later tools session that adds
  a network import would make it false, and nothing in the tools' own
  lane would notice. **Scope hints:** a new test file, or
  `test_pack_opener.py`. Order doesn't matter.
- **What:** pin TARBALL.md §5.10's copy of the shape sentence (with its
  second half) in `test_doc_crossrefs`, beside `EVERY_TURN_SENTENCE`.
  **Why:** the ruling now lives in three homes (opener, CLAUDE.md §3,
  TARBALL.md §5.10), and the suites pin only two. Only this session's
  `validation.sh` checked the third. **Scope hints:**
  `tests/test_doc_crossrefs.py` `TerminalShapePins`. It could ride the
  doc-injection sweep, which rewrites these docs anyway.
