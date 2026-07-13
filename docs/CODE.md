# CODE.md

> Code organization and refactoring philosophy.
> Read when `CLAUDE.md`'s INDEX says so.
> For the *why* behind any of this, see `CLAUDE.md`.

---

## META

### What this doc is

The vocabulary and decision rules for how code is organized: when
content earns extraction, what categories of code-unit exist and
how each behaves, when to introduce more structure, and how to
keep what exists honest. `CLAUDE.md` section 6 covers the *values*
— maintainability, tests-ship-with-code, no silent skips. This doc
covers the *layout decisions* that make those values concrete in a
specific codebase.

Some overlap with `CLAUDE.md` section 6 is deliberate: the layout
choices reinforce the same values they encode. Where the two files
overlap, both agree; if they conflict, this file wins on layout
questions and `CLAUDE.md` wins on values.

### Inscribed for Claude

Claude is the primary reader of this file and the writer of the
code it governs. CODE.md is written to be loaded before a layout
decision and acted on directly — fewer rhetorical defenses, more
triggers and signals. The architect reviews the result, not the
procedure. If a rule here is phrased in a way that doesn't
translate to action, that's a fix to land in a follow-up session.

### Conflict resolution

If something here conflicts with what Claude remembers from a
prior session, **this file wins.**

---

## INDEX

### Read paths

| Situation | Load |
|-----------|------|
| Deciding whether to extract a function or section | Sections 1, 4 |
| Deciding whether a file should split | Sections 1, 4, 5 |
| Adding an index header to a long file | Section 2 |
| Adding code to an existing file | Section 3 |
| Pruning dead code | Section 6 |
| Working on a codebase Claude did not author | Section 7 |
| Working on code that runs in or operates on the workflow itself | Section 8 |
| Naming a function, file, or section | Section 9 |
| Hard rules / what counts as a violation | Sections 10, 11 |
| Placing tests, or deciding where test code lives | Section 13 |

---

## 1. The Code Unit Inventory

Vocabulary of structural units. Each has a purpose, a lifecycle,
and a signal it has outgrown itself.

| Unit | Purpose | Outgrown when |
|------|---------|---------------|
| **Function** | One named action or value | It does two things; or its body is long enough that the next reader scrolls to find the end |
| **Section** (within a file) | A cohesive cluster of functions or classes under a banner header | Has its own internal sub-clusters; or readers reach for it without needing anything else in the file |
| **File** (module) | A subject — pack pipeline, parser, config loader | Holds multiple unrelated subjects; or sessions regularly load only part of it |
| **Package** | A subsystem whose subject can no longer be held in one file | The file's job is no longer expressible in one sentence |

A project starts at the smallest unit that works. Section before
file. File before package. Each next level earns its place;
nothing is introduced because it might be needed.

If a piece of code doesn't fit any unit — most often a
script-with-helpers that isn't quite a module yet — that's a
signal, either of an unrecognized pattern or a unit that hasn't
earned a name. **Don't invent a new category silently;** propose
it in `notes.md` and let the architect ratify.

---

## 2. Index Headers

A long file deserves a navigation map at its top, parallel to
`INDEX.md` for the project.

### 2.1 When to add one

- The file has 3+ sections demarcated by banner comments.
- A future session would otherwise scan or grep to find a
  section.

Below the threshold, a single top-of-file docstring describing
the file's job is enough.

### 2.2 Format

The index lives in the file's top docstring or top comment block,
listing every section with its name and an approximate line
number:

```python
"""bale — Claude session orchestrator.

Sections:
  1. Imports + constants       (~line 45)
  2. Logging                   (~line 167)
  3. Shell / git helpers       (~line 254)
  ...
"""
```

Line numbers are approximate; they drift as the file grows. Drift
of ±20 lines is fine because the banner comments themselves are
exact-match-searchable anchors. If a section moves more than ~50
lines from its listed position, the header is updated in the same
response.

Banner comments demarcate each section in the body:

```python
# ---------------------------------------------------------------------------
# 2. Logging
# ---------------------------------------------------------------------------
```

Numbered sections (`2. Logging`, not just `Logging`) make the
docstring's listing match the body 1:1 — the reader can jump by
number rather than name.

### 2.3 The non-negotiable rule

**A section isn't navigable until the index lists it.** Adding a
section without updating the header is the same as not adding it
— a future reader scanning top-down doesn't know it exists. Every
change that adds, removes, or renames a section also updates the
header in the same response.

A project that wants this rule mechanically enforced has Claude
include the header-coherence assertion in each response's
`validation.sh`. Bale itself does not enforce it.

---

## 3. Adding Code

Decision tree, in order.

### 3.1 Does this need to be extracted at all?

Default: **add the new code inline in the existing function or
section.** A new function, file, or layer is the right answer
only when:

- The same logic is needed in 2+ places.
- The piece has multiple distinct callers with different
  concerns.
- The piece is large enough to bury the surrounding logic.
- The piece has a different lifecycle than its host (a pure
  utility added to a stateful pipeline, for example).

If none apply, inline is correct. Over-extraction is a real cost:
scattered cognition, more file-jumps, more import lines for the
next reader to absorb.

### 3.2 Which unit fits?

Per section 1's inventory. Most additions are:

- **A function inside an existing section.** The default.
- **A new section in an existing file** when the addition begins
  a new subject the existing sections don't host.
- **A new file** when section 4's split signals are present.

### 3.3 Update the index header

If the file has an index header (section 2), every addition that
creates or renames a section updates the header in the same
response.

---

## 4. Splitting and Extracting

### 4.1 Signals that a function should be extracted from its host

- A block of 10+ lines that has a clear single responsibility
  and a name that would fit on it.
- A block called from 2+ places, about to become duplicated.
- A block that obscures the host function's intent — extraction
  lets the host read top-down at one level of abstraction.

### 4.2 Signals that a section should split into its own file

- The section is ~300+ lines AND has 2+ internal sub-clusters.
- Typical sessions touch the section without touching
  neighboring sections.
- The section has a separable surface — most other sections in
  the file talk to it through ≤3 entry points.
- A reader who knows the file would say *"this belongs in its
  own place by now."*

### 4.3 Signals that a file should split into a package

- The file is ~1500+ lines AND has 4+ sections that don't share
  readers.
- Internal coupling is now multi-section — one section calls
  many others — and a package layer would clarify the structure.
- The file's job is no longer expressible in one sentence.

These are *signals*, not thresholds. A 2000-line file with one
clear subject is fine; a 600-line file with five unrelated
subjects is not. Line count is corroborating evidence, not the
trigger.

### 4.4 The split procedure

1. Identify the cleanest internal seam. The lighter side stays
   where it was; the heavier side moves.
2. Extract the unit. Imports updated, callers updated.
3. Update the index header (and `INDEX.md` if the move creates a
   new file the project's doc inventory tracks).
4. Update any explainer doc that referenced the old structure.
5. Mention the split in `notes.md` of the tarball that does it.

### 4.5 When a split would be wrong

- The two halves would always be read together. No drill-down
  benefit, just two files instead of one.
- The proposed lighter unit would be too thin and wouldn't earn
  the separation (under ~30 lines for a function, under ~100
  lines for a section, under ~300 lines for a file).
- The seam isn't real. If Claude struggles to decide which side
  a piece goes on, the seam is wrong and the split shouldn't
  happen yet.
- The split would require contortions in the language's module
  system (circular imports, awkward re-exports). Fix the surface
  first; split later.

---

## 5. The Package Question

When a single-file script grows toward a multi-file package.

### 5.1 The threshold

A single file is correct until **all three** apply:

1. The file exceeds ~1500 lines AND section 4.3's signals are
   present.
2. Indexing (section 2) and section-level discipline can no
   longer extend the single-file lifetime.
3. The cost of the package layout — import machinery, install
   layout changes, packaging steps — is lower than the cost of
   continued single-file work.

If only (1) is true, indexing alone can usually extend the
single-file lifetime considerably. If (2) is also true but (3)
isn't, the right move is often a section-level split into one or
two sibling files rather than a full package layer.

### 5.2 Mechanics

When a single-file script becomes a package:

- The entry point stays where it was and becomes thin: parse
  args, dispatch.
- Implementation moves to a sibling library directory (the name
  follows the language's convention).
- Imports go through that directory.
- Install layout, upgrade flow, and any on-disk references update
  in the same session.

This is invasive — the install path, the upgrade path, and the
on-disk layout all change. A session that does this is dedicated
to the move, with no other concurrent feature work.

---

## 6. Pruning Code

Dead code is documentation that lies. Remove it.

### 6.1 What's prunable

- Functions with no remaining callers.
- Code paths gated by flags that have been removed.
- Commented-out blocks kept "for reference" past one session.
- Imports no longer needed after a refactor.

### 6.2 What's not prunable

- Code that looks unused but is part of a public surface (CLI
  entry points, library exports, schema fields, hook contract
  surfaces).
- Compatibility shims that may still be hit by old data, old
  tarballs, or old configurations.
- Anything where grep-for-callers can't fully establish
  unreachability.

Lack of recent use is **not** sufficient. Some code is
infrequently exercised but load-bearing when it is.

### 6.3 Procedure

1. **List candidates in `notes.md`** with the criterion for each
   — "no callers in current source," "flag removed in session
   N," etc. Don't act yet.
2. **Check callers** within the project and as much as possible
   across known consumers.
3. **Choose remove or keep** per candidate. When in doubt, keep.
4. **Declare in the manifest** — every removed function or block
   is declared in `changes[].reason` with the criterion that
   justified removal.

### 6.4 When to prune

- **Opportunistic** — during a tarball already touching the
  area, obviously dead neighbors go in the same response,
  declared. The same in-scope discipline section 7 covers
  applies.
- **Periodic sweeps** — whole sessions dedicated to pruning, no
  feature work mixed in.
- **Not during active feature work** — pruning while building
  risks removing something needed twenty minutes later.

---

## 7. Working on Code Claude Didn't Author

A separate framing applies when the project predates this
workflow, or has substantial code Claude is collaborating with.
The framing is less restrictive than it might sound: the
philosophy applies; only scope discipline tightens.

### 7.1 Apply the philosophy as you touch

Code Claude adds or modifies in a human-authored area takes
Claude's structural standard, not the surrounding code's. If a
function Claude is modifying would benefit from extraction per
section 4.1, extract it. If the section Claude is adding to would
benefit from an index header per section 2.1, add one. Local
inconsistency with surrounding untouched code is acceptable —
the codebase is converging toward philosophy, not frozen in
place.

### 7.2 Match surface, bring structure

Two kinds of convention, treated differently:

- **Surface** — naming style (snake_case vs. camelCase),
  indentation, formatter choices, language idioms. **Match the
  surrounding code.** If lint or a formatter would enforce it,
  match it. Surface inconsistency adds diff noise without
  earning anything.
- **Structural** — extraction, sectioning, indexing, function
  decomposition. **Bring this doc's philosophy.** These are
  decisions about where code lives and how it's organized; the
  philosophy is what the architect signed up for.

### 7.3 In-scope only

Opportunistic philosophy-application stays inside the files the
session is already touching. A session that modifies `foo.py`
may also apply philosophy within `foo.py`; it does not range
across `bar.py` and `baz.py` looking for improvements.
`CLAUDE.md` section 6's "stay in the lane" rule is the cap.

### 7.4 First-pass restraint

The first time Claude touches a file in a human codebase, the
response covers:

1. The requested change, applied cleanly.
2. Philosophy applied to the function or section being modified.
3. Observations in `notes.md` on what else in the touched files
   could be improved later.

Subsequent sessions act on what was surfaced. The point is a
converging codebase across sessions, not a sprawling reformatting
pass on first touch.

### 7.5 Disclosure obligation

Every philosophy-driven change to human-authored code is
declared:

- In `manifest.changes[].reason` — the reason explicitly names
  what the structural change is, not just what feature it
  supports.
- In `notes.md` when non-trivial — extractions, section
  additions, index headers, dead-code removal.

The architect sees what was touched and why on review. Surprises
in the diff are bugs.

### 7.6 Cross-file restructuring still requires invitation

Section 4.2's signals (section becoming its own file) and
section 4.3's signals (file becoming a package) are too big for
opportunistic application — they stop and surface. The line:
in-place philosophy is welcome; cross-file restructuring waits
for an ADR or a dedicated session.

### 7.7 The side effect — philosophy debt

`notes.md` observations accumulate, across sessions, into an
implicit map of where the codebase still diverges from this
doc's philosophy. The architect can scope future sessions
against that map — *"session 023 is the cleanup pass on
`parser.py` based on the last four sessions' notes."* This is
the rationale for why first-pass restraint isn't permanent: the
surfaced items don't get lost, they accrue.

---

## 8. Meta Code

Code that is part of, or operates on, the Claude workflow itself
— bale, hooks, response-handling helpers, validation harnesses,
anything that runs *during* pack or apply. The recursion changes
a few rules.

### 8.1 The one-apply-behind property

Any change to meta code takes effect on the *next* session, not
the session that lands it. A bug introduced lands silently in
session N and surfaces in session N+1. A fix to a bug lands in
session N, but session N's own pack and apply ran under the
buggy version. A `validation.sh` pass is a hypothesis test on
the *new* code; it is not evidence about the old code's behavior
on this session.

Sessions on meta code should expect the old behavior on the way
out and assert against the new behavior on the way in.

A project-local explainer carries the worked examples of how
this has shown up. CODE.md states the *property*; the project
doc carries the *history*.

### 8.2 Defense in depth

Mode bits, executable headers, manifest correctness, file
presence — meta code checks these at every step in the pipeline
it owns. A bug here has cascade potential: the broken tool
produces broken next-session input, which is much more expensive
to debug than a contained failure.

`validation.sh` in meta-code sessions includes change-specific
assertions even when they feel paranoid. The cost of a missed
assertion is a multi-session debugging arc; the cost of an extra
assertion is two lines of bash.

### 8.3 The reinstall (or equivalent) is load-bearing

A meta-code project that has a post-apply reinstall step — or
any equivalent that promotes the just-merged code to the version
that runs the next session — must not be skipped. Every skip
leaves the running tool one session behind the repo. The gap
compounds.

### 8.4 Refactoring meta code

Section 4's signals apply, with a wrinkle: a structural refactor
of meta code lands its breaking-change risk one apply later. A
session that does a structural refactor:

- Is dedicated to the refactor, not mixed with feature work.
- Uses the *next* session, not the same session, to confirm the
  refactor is working end-to-end.
- If the refactor changes the workflow's protocol shape, runs a
  small follow-up session that exercises the new shape before
  anything substantive is built on top.

This is the meta-code analogue of `CLAUDE.md` section 6's
"contracts are non-negotiable under time pressure" — the
recursion magnifies the cost of a confidently-wrong refactor.

---

## 9. Naming Conventions

Strict enough to be predictable; loose enough not to be a tax.

- **Match the surrounding code's conventions.** If the project
  uses `snake_case`, use `snake_case`. If a directory uses one
  casing, follow it. Surface consistency is enforced by lint and
  formatters anyway; matching is cheap.
- **Private helpers.** Match the language's idiom — leading
  underscore in Python, lowercase in Go, and so on.
- **New files.** Match the project's existing file-naming
  pattern (often `lowercase-hyphenated` or `snake_case`).
- **If tempted to invent a new pattern, don't.** Use the closest
  existing pattern and note the awkwardness in `notes.md`.

---

## 10. Hard Rules

Bale is project-agnostic and does not enforce code-layout rules
itself. The mechanical checks in the table below run in the
response's `validation.sh` — Claude includes the corresponding
assertions per-session for projects that adopt this doc's
philosophy. The universal bale-enforced rules live in `TARBALL.md`
section 8, which owns their enumeration.

| Rule | Type | Enforcement |
|------|------|-------------|
| Index header lists every section — a section isn't navigable until listed | contract | response's `validation.sh`: every banner in the file has a header entry; every header entry resolves to a banner |
| Splits and extractions are declared — restructuring shows in the manifest and `notes.md` | policy | review |
| In code Claude didn't author, structural changes are visible in `manifest.changes[].reason` | policy | review |
| Cross-file restructuring waits for an ADR or dedicated session — never opportunistic | policy | review |
| Meta-code sessions include change-specific assertions in `validation.sh` | policy | review |
| Pruning is always declared — every removal has a reason naming its criterion | contract | response's `validation.sh`: deletes have non-empty reasons |
| Don't invent code-unit categories silently — function/section/file/package is the vocabulary | policy | review |

Rule labels follow `CLAUDE.md` section 6 — contract rules are
caught mechanically; policy rules are caught at the architect's
review. Claude surfaces policy concerns in `notes.md` precisely
because mechanical checks won't catch them.

---

## 11. Hard Nots

- **Not a style guide.** This doc covers where code lives, not
  how it's formatted or named at the token level. Those are
  project- and language-specific and belong in lint configs.
- **Not a license to refactor without scope.** Refactoring
  opportunities outside the touched files go in `notes.md`, not
  into the diff.
- **Not over-architected.** Build a new layer (function →
  section → file → package) when you need it, not when you
  anticipate needing it.
- **Not a substitute for taste.** The thresholds in this doc are
  starting points. If something feels wrong, surface it in
  `notes.md` and let the architect decide.

---

## 12. The Meta-Principle

Code organization is treated like documentation. A unit earns
its place — a function that isn't called isn't worth
maintaining. It gets refactored — when it grows mixed-purpose,
it splits. It gets removed — when it's dead and isn't serving
any session, it goes.

The check for *"should this become its own X?"* is: will a
future session reach for it independently, and would having it
separate make that reach faster than scrolling? If yes, extract.
If unsure, leave it inline; whether it deserves its own home can
wait until it's been touched a few times.

---

## 13. Testing

> **Provisional section.** This is the interim home for testing
> doctrine, sitting after the Meta-Principle by intent rather than
> as an afterthought: it is a lodger, not part of the
> code-organization arc above it, and it lifts out cleanly when it
> earns promotion to a standalone global `TESTS.md` (the fifth
> workflow doc). Placing it last keeps that future extraction a pure
> lift with no renumbering of §§1–12. The promotion trigger is in
> §13.4. The decision to defer `TESTS.md` and house doctrine here is
> recorded in each adopting project's ADRs (e.g., an
> `adr/NNNN-defer-tests-doc.md` in the project's ADR directory).

`CLAUDE.md` section 6 carries the value — *tests ship with code.* This
section carries the **layout** half of that value: where test code
lives, when a test unit has outgrown itself, and how testing relates
to the §1 code-unit inventory. It does not decide a project's testing
*strategy* — what the oracle is, how deep to dogfood, how fixtures are
built, how hermetic the suite must be. Those are per-project decisions
that go in ADRs (§13.5), because the right answer depends on what the
code under test does.

### 13.1 A test is a code unit

Tests obey §1's inventory like any other code. A single assertion is a
function-scale unit; a cohesive group of assertions over one subject is
a section; a subject large enough to load on its own is a file; a test
subsystem with shared harness and fixtures is a package. The same
outgrown-when signals (§1) and the same split signals (§4) apply. A
test file earns extraction from its host the moment a session reaches
for it without needing the rest of the suite, exactly as production
code does.

### 13.2 Where test code lives

Match the project and language convention first (§9). Absent one, the
default is **tests adjacent to the subject they exercise** at the unit
they cover: a per-module test file mirrors its module; an end-to-end or
integration harness that exercises the whole tool is its own subject
and lives in its own place. The signal that a flat test file should
split is the same as §4.2 for any section — it has crossed ~300 lines
*and* grown internal sub-clusters that don't share readers (e.g. fast
unit checks living next to slow end-to-end paths that a focused session
would rather load alone).

### 13.3 Tests ship in the same response (the layout consequence)

`CLAUDE.md` section 6 requires a test in the same response as the
function it covers, or a `notes.md` deferral naming why not. The layout
consequence: a session that adds a meaningful function adds (or extends)
the test unit that mirrors it, in the same `files/` mirror, under the
convention §13.2 fixed. A deferral is a `manifest.deferred[]` entry plus
a `notes.md` line — never a silent omission. When a whole line of work
defers its tests to a later phase (a harness that hasn't landed yet),
that deferral is named once in the project's design doc and repeated in
each interim session's `notes.md`, so untested code is always visible as
a known debt rather than an accident.

### 13.4 Promotion trigger — when this section becomes `TESTS.md`

This section stays a section until it crosses DOCS.md §6.1's own split
signals: it covers **multiple distinct topics that don't share
readers** — testing *philosophy*, *harness mechanics* (how to author a
selftest, the sandbox/fixture API), and *reference* — such that a reader
here for code layout scrolls past testing machinery they don't need. In
practice that threshold is reached when a project's end-to-end test
*harness* lands and its mechanics need documenting: at that point the
doctrine has a different reader (someone writing tests) and a different
lifecycle (it tracks the harness, not the code-layout philosophy) than
the rest of CODE.md. DOCS.md §11 is the governing rule — *write it as a
section first; its own file waits until it has been read a few times.*

Promotion is a documentation **split** (DOCS.md §6.2), and because
`TESTS.md` would be a global workflow doc, it carries one extra cost the
ordinary split doesn't: bale injects the global docs from its own
installation, so adding a fifth one means updating bale's `GLOBAL_DOCS`
set and the pack-time injection — a `bin/bale` change, hence its own
session. The split session does both: lifts §13 into `TESTS.md` (this
section becomes a one-line trigger pointing there, mirroring how the
INDEX read-paths table points at the heavier doc) and lands the
injection change.

### 13.5 Strategy is per-project — recorded in ADRs

The choices this section deliberately does not make — the test
**oracle** (what decides pass/fail), **dogfood depth** (how much the
suite drives the tool through its own surface vs. internal functions),
**fixtures** (how test inputs are built and maintained), and
**hermeticity** (how isolated the suite is from the real environment) —
are decided once per project and recorded as ADRs, because each answer
depends on the subject under test. A tool that operates on the developer's
own environment (installs, git state, a `$HOME`-level config) has a
sharp hermeticity rule that a pure library doesn't need; a tool that is
its own primary artifact (meta code, §8) has a dogfood-depth answer
shaped by the one-apply-behind property (§8.1) that an ordinary project
never faces. CODE.md states the property; the ADRs carry the project's
answer.
