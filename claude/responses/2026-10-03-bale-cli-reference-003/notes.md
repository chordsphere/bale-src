# Notes: 2026-10-03-bale-cli-reference-003

Every request bale builds now carries `BALE_HELP.md` at `request-NNN/`'s
top level, and the carried docs route to it. Below are the decisions I'd
like ratified, the count the BALE.md ruling asked for, and three paths
outside the forecast.

## What the reference is

- **What it holds.** The top-level `bale help`, then one section per
  command path (17 today, `config init` and `config hooks` included), in
  `bale help`'s listing order. Each body sits verbatim inside a code
  fence. A short header and a contents list come first. The file is about
  77 KB.
- **How it's rendered.** `bin/bale`'s `render_cli_reference()` builds a
  fresh parser and calls `format_help()` on each page with the
  formatter's width pinned to 78. argparse uses COLUMNS − 2, so 78 is
  what COLUMNS=80 produces. Color is forced off, and any SGR escape is
  stripped as a backstop. The result: every section equals
  `COLUMNS=80 bale help <verb>` byte for byte. That is also what a piped
  `bale help` prints, since 80 is argparse's fallback. I checked that a
  pack at COLUMNS=37, and renders at 30 / 200 / FORCE_COLOR=1, all
  produce identical bytes.
- **Carriage.** `build_request_tarball` writes the file right after the
  tools loop, so pack and handoff both get it from one site. It writes
  bytes, not text, so a Windows Python won't turn LF into CRLF.
  `CLI_REFERENCE_NAME` and `CLI_REFERENCE_COLUMNS` sit next to
  `CARRIED_TOOLS` in `bin/bale`.
- **Context tarballs** carry no reference. They don't go through
  `build_request_tarball`, and a test pins that.

## Decisions to ratify

1. **Name and place: `BALE_HELP.md`, top level.** It's ALL_CAPS like
   its siblings and says what it is: `bale help`. It doesn't trip the
   guard's `BALE.md` substring. The one cost is that a reader could
   confuse it with BALE.md. The carried docs never name BALE.md, so I
   judged that acceptable. I chose Markdown over plain text for the
   contents list. Each fence is sized one longer than the longest
   backtick run in its body, so help text can never close a fence early.
2. **Not in provenance.** `contract_docs` is for the five contract
   docs. The reference is generated from code that `bale_version`
   already pins, and where the two overlap, TARBALL.md stays the
   contract. A provenance key would also change the request-manifest
   schema, the lint's embedded copy, and the echo, all outside this
   forecast.
3. **Rendered inside `build_request_tarball`, not passed in by the
   callers.** This way no future caller can forget it. The cost is a
   two-line stub in `test_craft_response.py`'s partial-`__main__`
   driver (see departures below).
4. **The `stats` section is not install-only.** `bale stats`'s
   description names the packed repo's configured telemetry home
   (`StatsHelpFormatter`). So that one section reads as
   `bale help stats` reads in that repo, and two repos with different
   `[layout] agent_dir` produce different bytes. I read the brief's
   "byte-identical regardless of width" as width-independence and kept
   the help verbatim. If you want the reference install-pure, the fix
   is to substitute the default home during the render. It's a small
   change; say so and it goes in a follow-up.
5. **Guard scope.** The self-containment guard gains a rendered scan
   group. Everything outside the code fences (header, contents,
   headings) is held to the docs-and-tools deny table, all three
   halves. The fenced help bodies are exempt wholesale, so this session
   doesn't pre-empt the open ruling. A specimen test proves the strip
   removes only fenced bodies. I seeded `BALE.md, board 7` into the
   header in a scratch copy to confirm the guard fails on both shapes.
6. **No change to the opener or PLANNER.md.** AGENT.md's core, which
   every role reads in full every session, now names the file twice: in
   the META reachability paragraph and in an INDEX row. The opener
   doesn't enumerate the tarball's contents, so leaving the reference
   out of it contradicts nothing. An opener sentence would lengthen
   every opener and churn `test_pack_opener.py`, in a file session D is
   about to touch. PLANNER.md is outside the forecast anyway.

## The count for the BALE.md ruling

Generated at v0.4.45 from this tree. **24 occurrences of `BALE.md`
across 9 of the 18 sections** now ride every request:

- 22 are section citations, to 11 distinct sections: §5.4, §5.6,
  §6.7, §7.1, §7.3, §7.8, §8.1, §8.5, §8.9, §8.11, §11.
- 2 are bare mentions: the top-level epilog ("the full tool
  reference is BALE.md in the bale-src repository") and `handoff`'s.
- Per section: top level 2, pack 4, apply 8, retry 3, revert 2,
  handoff 2, unlock 1, open 1, stats 1.
- **8 board citations** also ride along, which the guard's board shape
  would flag in a doc: pack 2, apply 3, retry 2, amend-checkpoint 1.
  The ruling queue entry doesn't mention these, but a string pass would
  want them too.
- The top-level page repeats each verb's one-line summary, so relay's
  `(BALE.md §8.11)` rides once even though `bale help relay` itself
  cites nothing.

## Forecast departures (admit per path at apply)

- `tests/test_cli_reference.py` (created). The reference's own suite:
  verbatim against the real CLI, coverage checked against an
  independent parser walk, width and FORCE_COLOR independence, carriage
  by pack and handoff, absence from context tarballs, and the handoff
  reading-plan filter. A new test file sits outside any forecast by
  construction.
- `tests/test_craft_response.py` (modified). `PackCarriageSurface`
  drives `build_request_tarball` under a stub `__main__`, which now
  needs `CLI_REFERENCE_NAME` and `render_cli_reference`. Without the
  stub its two cases fail on ImportError.
- `tests/test_install_precheck.py` (modified). Its end-to-end pin
  asserted that the request's top-level `.md` set equals GLOBAL_DOCS
  exactly. It now expects GLOBAL_DOCS plus `BALE_HELP.md`. Its
  `contract_docs` check is unchanged.

None of these is on session A's forecast.

## Where to look closely

- `render_fixed_width_help` replaces the parser's `formatter_class`
  with `functools.partial(..., width=78)`. argparse only ever calls
  `formatter_class(prog=...)`; I verified that on 3.13, the only
  Python in this sandbox. 3.14 adds a color step after construction.
  The render turns it off through `parser.color` and strips escapes as
  a backstop, but that path is reasoned, not run. The function mutates
  the parser, which is why `render_cli_reference` builds its own.
- The handoff reading-plan filter now skips `BALE_HELP.md` like the
  global docs, so a plan citing it doesn't try to pull it from the
  repo. The handoff e2e test cites it in the plan and checks it ships
  once, at the top level.

## Validation, and what I couldn't see

The request's `context/` is a partial bale-src tree. Six tests fail in
it **before and after** this change. Each depends on files the context
didn't ship: three in `test_include_group` need the repo's
`bale.toml`, two in `test_changelog_record` need the changelog corpus,
and `test_doc_crossrefs`'
`test_adr_0013_citations_carry_resolving_keys` needs ADR-0013. Results
with this change applied:

- Full discover: the same six fail, nothing else.
- Full discover with `BALE_TEST_SLOW=1`: the same six fail, nothing
  else.

The validation group that includes `test_doc_crossrefs` is therefore
claimed `pass` with basis `predicted`, not `observed`. In your staging
copy ADR-0013 exists, and I expect it to pass. The full discover sits
behind `--slow`, claimed `untested`.

Per §7.2, I ran `validation.sh` on the unmodified tree too. Both test
groups fail there, and so do both reference assertions. The constraint
guards (no `BALE_HELP.md` file in the tree, BALE.md not in the change
set) and the exec-bit assertions pass on both trees, as regression
guards should.

`model_identity` is this session's configured model id. The surface
doesn't let me confirm the serving model, so treat it as configured
rather than verified.

## Proposals

**What.** Sentences for the 99b BALE.md true-up (BALE.md is out of
scope here):

- §3.3, after its first paragraph: "Beside them, every request carries
  `BALE_HELP.md`, the installed bale's `bale help` for every command.
  It is not an install file: `render_cli_reference()` writes it from
  `build_parser()` when the request is built, at a fixed 80 columns,
  so it is version-true by construction and identical from any
  terminal."
- §3.3, the pin sentence: append "and the generated reference's
  framing (everything outside its code fences) is scanned by the same
  guard's rendered group; the fenced help text is exempt pending the
  ruling on BALE.md citations in help strings."
- §6.1's shape block: add
  `BALE_HELP.md         # generated by bale at build time: bale help for every verb`.
  The block is also missing `PLANNER.md`, which joined at v0.4.11; the
  true-up could add both.
- §7.5 step 3: append "and the generated CLI reference
  (`CLI_REFERENCE_NAME`), rendered by `render_cli_reference()` and
  written at the request's top level."
- §5.1: add "Every request carries the full set as `BALE_HELP.md`
  (§6.1)."

**Why.** BALE.md describes the request shape and the build steps.
Without these sentences it understates what ships from this version on.

**Scope hints.** BALE.md only. It needs nothing from this session
beyond the names above.

**What.** Fold the ruling's eventual string pass over the 8 board
citations too, not just the 24 BALE.md ones.

**Why.** They travel in every request now and dangle just the same.
A doc would fail the guard's board shape on them.

**Scope hints.** `bin/bale`'s help strings. Once the citations are
gone, the guard's rendered group could tighten to scan the bodies as
well. `CliReferenceFramingSelfContainment` is where that would land.
