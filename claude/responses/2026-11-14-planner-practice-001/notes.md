# Notes: 2026-11-14-planner-practice-001

The eight lines are in docs/PLANNER.md, each with its phrase verbatim,
and 0.4.61 is cut. Nothing in the brief was unclear enough to stop on,
so there was no probe and no light block. What follows is what I
decided where the brief left room, where I went a step past the slips,
and what I would look at first.

## Where each line went

Line numbers are docs/PLANNER.md as landed.

| Outcome | Section | Line | Bold lead |
|---|---|---|---|
| 1, the wrapping tool's line (and the gh item) | 2 | 144 | A planner working through a tool that wraps bale hands the packer the wrapping tool's line, never bale's. |
| 2, no backtick and no dollar sign | 2 | 166 | A line a planner hands a person to paste holds no backtick and no dollar sign inside its double quotes. |
| 6, paste blocks and lists | 2 | 176 | A paste block never sits inside a list item. |
| 5, a successor's stem | 2 | 193 | A successor's bundle takes a stem no earlier bundle of its slug had. |
| 3, a showing's first light block | 6 | 625 | A sitting whose goal is a showing asks in its first light block when, for whom, what must be live and what may be not yet. |
| 7, defaults about the packer's world | 6 | 635 | An as-assumed default about the packer's machine or a remote's state is probed, not assumed. |
| 4, byte greps | 6 | 645 | A planner probe that greps for a byte pattern runs it under `LC_ALL=C`. |
| 8, showing the plan | 6 | 653 | A sitting shows the plan and its place in it, at its start and whenever either changes. |

The sitting guessed section 2 for the paste and command lines and
section 6 for the sitting lines, and that is where they are. Each
phrase sits whole on one physical line, though the brief did not ask
for that.

## Decisions to ratify

- **One INDEX row.** PLANNER.md's read paths send a sitting to section
  6 alone, and three of the section 2 lines (the wrapping tool's line,
  the no-backtick line, the paste-block line) bind a sitting every time
  it hands something over, pack or no pack. So line 71 is a new row:
  "Handing the packer a line or a block to paste: Section 2". If you
  would rather the sitting row read "Sections 2, 6", it is a one-line
  change.
- **One cross-reference in TARBALL.md 3.4**, as the sitting guessed. The
  goal-string paragraph now ends with a sentence pointing at PLANNER.md
  section 2. I added it as two lines of its own after "the same
  hazard." instead of rewrapping the paragraph, so that line stays
  short. That keeps the whole session to insertions, which is what
  lets validation prove nothing else moved.
- **tests/ is untouched.** I read the suites that pin the docs
  (crossrefs, self-containment, noun, sanctioned pairs). None pins
  PLANNER.md's bytes or its section list in a way these insertions
  break. The one order pin, that the bundle bullet comes before
  "Commands are single-line", still holds with the wrapping-tool
  bullet between them. I read the brief's "follow it" as opening
  tests/ for existing pins only, so I added none. See Proposals.
- **The changelog record lists the two docs as its surfaces.** A
  doc-only release has no machine-readable surface in the strict
  sense, but 0.4.60's record carries a docs/TARBALL.md row, the suite
  requires a record for every bin/VERSION, and the brief asks for one.
  Its `at` is 2026-11-14T14:45:00+00:00, the session's clock when I
  wrote it.

## Where I went past the slips

Three sentences are mine, not the slips'. Each closes a gap the bare
rule would have left, and each is yours to strike.

- **Line 1 says where the wrapping tool's line comes from.** "Never
  bale's" leaves a planner who was not told the wrapping tool's line
  with nothing to hand over, and the tempting move is to guess a
  spelling. The line says: take it from what the request carried,
  never from memory, and given none, say so and name the bundle,
  nothing more. That matches the slip's own picture, where the tool
  offers the bundle itself.
- **Line 3 says the showing's questions are three.** The phrase reads
  as three or four items, and the light tier refuses a fourth question
  (TARBALL.md 5.10). The line says the live and not-yet split is one
  line drawn, so a sitting does not emit a block that fails admission.
  It also defines a showing ("work put in front of someone on a day"),
  which is my reading of the slip's four words. The gaps list the slip
  cites did not ride with the request, so check that definition.
- **Line 4 gives the reason for `LC_ALL=C`.** The slip gives the rule
  only. I checked the reason against GNU grep 3.11 before writing it:
  under a UTF-8 locale a byte range past ASCII matched nothing and said
  nothing, and a file with one invalid sequence came back as "binary
  file matches". Under `LC_ALL=C` both worked. The line says "can" and
  "may", since other greps differ.

Two smaller things in the same vein:

- **"For the courier" is the slip's phrase, kept as given.** I did not
  say who the courier is under a wrapping tool, because that is the
  tool's business and differs by tool. The line says only that the
  `bale open` line still travels with the bundle and is not what the
  packer is told to type.
- **No line names its traffic.** PLANNER.md section 8 keeps provenance
  project-side, so the four lines from the walkthrough say "earned at
  a live walkthrough", the no-backtick line says two lines written for
  a wrapping tool's verb carried backticked command names, and nothing
  carries a date, a session or a ledger item.

## Validation

validation.sh runs eight checks. Six are the session's own: file
syntax, the eight phrases each in its section, the successor sentence
against the crafter's `--bundle` help, PLANNER.md naming no office,
the insertions-only proof, and the release. The seventh is eight of
the project's suites, the ones that read the docs, bin/VERSION or the
changelog (about 13 seconds). The eighth is the whole suite, behind
`--slow`.

I ran it on both trees, as TARBALL.md 7.2 asks. On the tree with the
change everything passes. On the unmodified tree five of the six
session checks fail, which is what they are for. Two pass on both and
are guards by design: "PLANNER.md names no office" (the brief pins
that the word is absent before and after) and the project suites.

The insertions-only check removes the 84 inserted lines from
PLANNER.md and the 2 from TARBALL.md and hashes what is left against
the base hashes your request stamped. So "no existing line changed" is
proved against your bytes, not asserted.

The whole suite is claimed `untested`, because apply skips it unless
`--slow` is passed. I did run it here on the changed tree: 2208 tests,
48 skipped, OK, 589 seconds. That is the brief's count at 0.4.60, as
it should be for a session that adds no test.

## Something I noticed

tools/craft_response.py line 3066 has a source comment that names
office-src and one of its ledger items, in a tool that rides with
every request. It is a comment, not help text, and no guard denies it.
It is outside this session's lines, so I left it. If "naming none" is
meant for the carried tools as well as PLANNER.md, that comment is the
one place I saw.

## Proposals

- **What.** Pin the eight phrases in the suite, each against its
  PLANNER.md section, and hold the successor sentence to the crafter's
  own constant so the doc and the help cannot drift apart.
  **Why.** Today only this session's validation.sh checks them, and it
  runs once. The crossrefs suite already pins other verbatim sentences
  this way, and tests/test_probe_scaffold.py pins the help's copy of
  the successor sentence but not the doc's. A later doc session that
  rewraps or rewords section 2 or 6 would pass every suite.
  **Scope hints.** tests/test_doc_crossrefs.py, or a small suite beside
  it. No ordering dependency.
- **What.** Decide whether "PLANNER.md names no tool that wraps bale"
  should be a standing guard, and if so add a deny row to the noun
  guard.
  **Why.** This session's check for it lives in validation.sh and goes
  away with the session. The rule is a ruling about the doc's future,
  which is yours and not mine to add on my own.
  **Scope hints.** tests/test_global_doc_noun.py, scoped to
  docs/PLANNER.md. It needs the list of names to deny, which only you
  have.

## Handbook

### bale-src

- Since 0.4.61 docs/PLANNER.md carries eight planner practice lines from the slips: four in section 2 (the wrapping tool's line, never bale's; no backtick and no dollar sign inside a pasted line's double quotes; a paste block never sits inside a list item; a successor's bundle takes a stem no earlier bundle of its slug had) and four in section 6 (a showing's first light block; an as-assumed default about the packer's machine or a remote's state is probed, not assumed; byte greps under LC_ALL=C; a sitting shows the plan and its place in it).
- Since 0.4.61 docs/PLANNER.md's INDEX read paths carry a row sending a line or a block handed to paste to section 2, and docs/TARBALL.md 3.4's goal-string paragraph ends with a sentence pointing at PLANNER.md section 2.
- 0.4.61 is doc only: it changes docs/PLANNER.md, docs/TARBALL.md, bin/VERSION and claude/changelog/0.4.61.json, every doc edit an insertion, and no code, test, schema or tool.
- No suite test pins the eight 0.4.61 practice phrases in docs/PLANNER.md or holds its successor sentence to the crafter's constant; only that session's validation.sh checked them.
- docs/PLANNER.md does not contain the word office at 0.4.61, and no other global doc under docs/ does either.
- The whole unit suite runs clean in a worker sandbox at 0.4.61: 2208 tests, 48 skipped, about 10 minutes; the eight modules that read the docs, bin/VERSION or the changelog (test_doc_crossrefs, test_global_doc_selfcontainment, test_global_doc_noun, test_sanctioned_pairs, test_changelog_record, test_release_packaging, test_contract_verb, test_cli_reference) take about 13 seconds.

#### Front sheet

bale-src is the source of bale, the occupant's command-line tool for
handing work to an agent session and taking the result back. bale packs
a request tarball, carries the worker's questions and the planner's
answers through `bale relay`, checks the response tarball the session
returns, and lands it on a branch in the project only after validation
passes. On 2026-11-14 it stands at 0.4.61 once this session lands, the
fifth of eleven releases planned in folder 43 for the slips about bale.
This release changes words only: PLANNER.md, the planner's manual that
rides with every request, gains eight lines of practice from the slips,
written for any tool that wraps bale and naming none.

## Walkthrough

### What changed

- **docs/PLANNER.md, section 2 (authoring commands).** Four new
  bullets. A planner working through a tool that wraps bale hands over
  that tool's line, not bale's. A line handed to someone to paste has
  no backtick and no dollar sign inside its double quotes. A paste
  block never sits inside a list item. A successor's bundle takes a
  stem no earlier bundle of its slug had.
- **docs/PLANNER.md, section 6 (sitting practice).** Four new bullets.
  A sitting planning a showing asks first when, for whom, what must be
  live and what may be not yet. A default about the packer's machine
  or a remote is probed, not assumed. A probe that greps for bytes
  runs under `LC_ALL=C`. A sitting shows the plan and its place in it.
- **docs/PLANNER.md, INDEX.** One new row in the read-paths table.
- **docs/TARBALL.md, 3.4.** One sentence at the end of the goal-string
  paragraph, pointing at PLANNER.md section 2.
- **Release.** bin/VERSION is 0.4.61, and claude/changelog/0.4.61.json
  is its record.

Nothing else changed. No existing line of either doc was edited, and
no code, test, schema or tool was touched.

### Why

- Five slips recorded planner practice that lived only in chats and in
  one office's notes. PLANNER.md is the one place a planner in any
  project reads, so that is where practice has to be written to stick.
- The slips were written about one wrapping tool. PLANNER.md travels
  to every project, so each line is worded for any tool that wraps
  bale and names none.
- The fifth slip held five items. Three became lines, the gh item
  folded into the first line, and the forcing refspec was left out, as
  the plan ruled.

### How to explain each piece

- **The wrapping tool's line.** "If you reach bale through another
  tool, the planner gives you that tool's command. The `bale open`
  line still comes with the bundle, but it is not the one you type."
- **No backtick, no dollar sign.** "Inside double quotes the shell
  runs backticks and expands dollar signs before the command sees
  them. So a line you are given to paste has neither. TARBALL.md
  already said this for the goal; now it holds for every pasted line."
- **Paste blocks and lists.** "A block inside a list item picks up the
  list's indent, and that breaks a heredoc. So blocks to paste stand
  on their own, outside lists."
- **A successor's stem.** "A new bundle for the same slug needs a file
  name stem no earlier one had. Otherwise a tool that tracks opened
  bundles by stem thinks it has seen the new one."
- **A showing's first questions.** "If the goal is to show something
  to someone, the sitting asks at the start when, to whom, and what
  must work versus what can wait. The plan is built from those
  answers."
- **Probed, not assumed.** "A light block's default is fine for a
  decision. For a fact about your machine or a remote, the sitting
  sends a probe instead of offering a guess to ratify."
- **Byte greps.** "A probe that searches for bytes sets `LC_ALL=C`, so
  grep means bytes on any machine."
- **Showing the plan.** "The sitting shows the steps and which one
  this is, at the start and whenever that changes."

### Questions a reviewer will ask

- *Why are the lines split across two sections?* Section 2 is about
  what a planner hands over (commands, bundles, blocks). Section 6 is
  about how a sitting runs. The new INDEX row sends a sitting to
  section 2 when it hands something over.
- *Did anything already in PLANNER.md change?* No. validation.sh
  removes the inserted lines and checks the rest against the hash the
  request stamped for the file.
- *Why touch TARBALL.md?* The no-backtick rule now has two homes: the
  goal string in TARBALL.md 3.4 and every pasted line in PLANNER.md
  section 2. One sentence ties them together so neither reads as the
  whole rule.
- *Why no new tests?* The brief opened tests/ only for following pins
  that already exist, and none needed following. A suite pin for the
  eight phrases is proposed for a later session.
- *Is the successor sentence the same as the help's?* Yes, byte for
  byte. validation.sh compares the doc with tools/craft_response.py.
- *Does any line name the office?* No. The word does not appear in
  PLANNER.md, and validation.sh checks that.

### A hand test

Only eyes can say whether the lines read as rules a planner on any
tool could follow. Run these in the bale-src checkout, on the branch
where the session landed.

1. Run `cat bin/VERSION`. It prints the release number, and should
   show `0.4.61`.
2. Run `grep -n "wrapping tool's line" docs/PLANNER.md`. It finds the
   first new bullet, and should print one line, numbered 145.
3. Open docs/PLANNER.md at line 144 and read down to line 201. These
   are section 2's four new bullets, with two older ones between
   them. Check that each reads as a rule you would want a planner on
   any tool to follow, and that the sentence about where the wrapping
   tool's line comes from (lines 152 to 155) is one you agree with.
4. Open the same file at line 625 and read down to line 662. These are
   section 6's four new bullets. Check that "a showing" as lines 626
   and 627 define it is what you meant by it, and that calling its
   questions three (line 631) is right.
5. Run `grep -c -i office docs/PLANNER.md`. It counts the lines that
   hold the word, and should print `0`.
6. Run `python3 tools/craft_response.py --help | grep successor`, then
   `grep -n "successor's bundle" docs/PLANNER.md`. The first prints
   the help's sentence and the opening of its reason, and the second
   prints the doc's sentence, at line 193. The two sentences should be
   the same.
7. Open docs/PLANNER.md in something that renders markdown and look at
   the Read paths table near the top. The second row should read
   "Handing the packer a line or a block to paste" and point at
   Section 2, as a proper table row.

## Structure

- title: Fix bale-src for the slips about bale, in eleven sessions
- size: high
- goal: Land the fixes to bale-src for the slips about bale in the office's suggestion box, one release per session, in the ratified order
