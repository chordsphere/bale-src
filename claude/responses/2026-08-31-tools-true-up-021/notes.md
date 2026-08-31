# notes — 2026-08-31-tools-true-up-021

## The chat-resolved round (durable record, per the desk's instruction)

Four questions went to the desk in chat before any editing; the rulings
are recorded here because chat is not durable and the reasoning binds
what the diff looks like.

1. **`ExchangeBlockParity`'s loader stays on `bin/bale`.** I flagged
   that the class loads `REPO/bin/bale` and reads `format_exchange_block`,
   `_exchange_body_bytes`, `_normalize_manifest_to_record` and the five
   constants off it, while `bale_relay.py`'s docstring says `bin/bale`
   consumes only `cmd_relay` — so retargeting the class prose to name the
   relay module risked describing something the code does not do. Ruling:
   board 59's retry record shows the extraction HOLDed on exactly those 17
   parity errors, and the ratified fix was a narrow re-export block in
   `bin/bale` carrying the wire surface (sentinels, trailer regex, sides,
   `_exchange_body_bytes`, `format_exchange_block`, `parse_exchange_input`,
   `_normalize_manifest_to_record`), each comment-marked with this suite as
   its consumer. The class is green today, deliberately. **The accurate
   retarget is provenance, not mechanism** — the vocabulary originates in
   `bin/bale_relay.py` (v0.4.21) and reaches the suite through `bin/bale`'s
   re-export. That is what the new prose says, and the loader is untouched:
   changing it would be a behavior change and would unpin the re-export
   contract the suite exists to guard.
2. **Nine sections, ratified.** Two added banners, seven existing names
   verbatim, `Imports + constants` as section 1 per `CODE.md` §2.2's own
   example.
3. **Test ids frozen.** Renaming `test_constants_match_section_29` /
   `test_normalization_matches_section_29` changes test identity, which is
   behavior for anything selecting by name. Each keeps its id and gains a
   docstring line saying the section-29 contract now lives in
   `bin/bale_relay.py`. The historical names are not false the way the
   `RE-DECLARED` citation was — they name a contract that moved, not a
   source that lies.
4. **Validation plan endorsed**, with the instruction to compute the
   digests from the request's shipped bytes rather than from memory of
   them. Done that way: `sha256` over a canonical AST walk of
   `request-021/tools/craft_response.py` and
   `request-021/context/tests/test_craft_response.py` as extracted.

The desk also corrected its own brief on two points, recorded here: the
"four" stale citations in the crafter came from a head-truncated grep
(the real count is seven, below), and the brief's "possibly the matching
citation in tests/test_craft_response.py" resolves, under ruling 3, to a
docstrings-and-comments-only sweep with ids frozen.

## What changed

**`tools/craft_response.py`** — all seven stale section-29 citations
retargeted, and the index header added.

The seven sites, since the brief expected four: the `--emit-block`
docstring bullet (was "byte-identical to section 29's"); the
`RE-DECLARED from bin/bale section 29` banner comment; the drift-guard
paragraph's "pins these constants against section 29's"; the
`exchange_body_bytes`, `format_exchange_block` and
`normalize_manifest_to_record` docstrings; and the "matching section 29's
dict literal exactly" line inside the last of those. The banner comment
and the drift-guard paragraph each gained a sentence carrying the
provenance ruling — the section is gone, the bytes are not — so a reader
who arrives at the constants understands why the file cites a module
rather than a section number, and why the parity suite imports through
`bin/bale` anyway. The drift-guard paragraph also now names
`validate.sh`'s crafter-vs-`bale_relay` row as the install-side subset,
which is the second prose home the brief said had drifted out of
agreement with this one.

The index header lists nine sections. Sections 3–9 are the file's seven
existing banners with their names verbatim and a number prefixed; 1
(`Imports + constants`, opened immediately after the module docstring so
`from __future__` stays the first statement) and 2 (`Shared helpers
(slug, log, exit)`) are new banners over the ~500 lines that previously
sat above the first banner and were therefore unlisted and unnavigable.
The listing sits at the top of the docstring, matching `CODE.md` §2.2's
shown format rather than trailing 200 lines below it.

**`tests/test_craft_response.py`** — the module docstring's guard
description, the `ExchangeBlockParity` class docstring, one inline
comment in `CraftEmitBlock`, and the two `_section_29` methods'
docstrings. The class docstring now says outright why `setUpClass` loads
`bin/bale` rather than the relay module, so the next reader does not
re-derive my question from scratch.

## One citation deliberately left

`tests/test_craft_response.py` still says "drifted from bin/bale section
29's" inside the `assertEqual` failure message in
`test_rendering_is_byte_identical`. That is a string literal, not a
comment or a docstring, so it sits outside the constraint's stated
surface — and check 3 below would fail on it, correctly, since a string
literal is executable content. Worth fixing in a session whose lane
admits it; proposed below.

## Validation

Four checks; the third is the mechanical form of the zero-behavior-change
constraint. Each file is parsed, every docstring node is *dropped* (so
adding one to `test_constants_match_section_29` is invisible, not just
edits to existing ones), comments never reach the AST at all, and a
canonical walk over an explicit field whitelist is digested. Both files'
digests are byte-identical to the originals'. I built the canonical form
from a whitelist rather than `ast.dump()` on purpose: `ast.dump()` emits
whatever fields the running Python defines, so a release adding a node
field would move the digest and produce a false FAIL. The check prints
the crafting interpreter's version (3.12.3) in its header for the same
reason — if it ever fails on a distant interpreter, rule that out before
reading it as a real code change.

Check 2 is the crafter's own `--doc-assertions --index-header` emission,
pasted rather than hand-written, per `CODE.md` §10. I ran it against the
edited file: `[PASS] index header coherent: tools/craft_response.py
(9 section(s))`.

## Claims, and the one that is only predicted

The suite claim is `predicted`, not `observed`, and it is the one thing
to watch. The request ships no `bin/`, so when I ran
`tests/test_craft_response.py` here, `ExchangeBlockParity` skipped —
which is exactly the class ruling 1 is about. What I could observe is
that the suite behaves *identically* before and after my edits (122 tests,
same 2 failures / 2 errors / 17 skips, all of them my sandbox's missing
`bin/` and `schemas/`, none of them mine). In a full checkout the parity
class runs and its verdict is real. The other two claims are `observed`.

Nothing landed outside the request's write forecast; both changed paths
are in `resolved_scope`.

## Proposals

- **Retire the last section-29 string literal.** `test_rendering_is_byte_identical`'s
  `assertEqual` message still names `bin/bale` section 29 as the drift
  source. *Why:* it is now the only stale citation left in either file,
  and it is the one a developer reads at the exact moment the guard goes
  red — the worst moment to be pointed at a section that no longer
  exists. *Scope hints:* one string in `tests/test_craft_response.py`; a
  behavior-surface change by this session's constraint, so it wants a
  lane that admits string literals. Cheap to fold into whatever session
  next touches that class.
- **Rename the two `_section_29` test ids.** `test_constants_match_section_29`
  and `test_normalization_matches_section_29` name a contract by its
  former address. *Why:* their docstrings now have to explain the name,
  which is the tell that the name is doing work the code no longer
  supports; a reader grepping `section 29` after the extraction finds
  test ids and concludes the section still exists somewhere. *Scope
  hints:* `tests/test_craft_response.py` only, but it changes test
  identity — anything selecting these by name (CI shards, a `-k` filter,
  the board's own retry records) moves with them, so it wants a session
  that can check those consumers rather than a comment-only lane.
- **Consider an index header for `tools/response_lint.py`.** *Why:* I
  noticed it while confirming the crafter's banner shape — the lint has
  its own multi-section body and no listing, so the rule this session
  just mechanized for one of the two shipped tools is unenforced on the
  other. I did not look closely enough to say how many sections it has or
  whether its banners are numbered; that is the session's first job.
  *Scope hints:* `tools/response_lint.py`; independent of anything here,
  and its `validation.sh` is a one-line change to this session's check 2
  (add a second `--index-header` path).
