# Notes — 2026-09-21-split-transition-unconditional-007

Everything is inside the forecast: four paths, all four forecast, no
departures. Bumpless as ruled. The three VERBATIM sentences shipped
without correction, and I did check them rather than take them on trust
(below).

## The VERBATIM sentences, checked against the facts

- **A** ("bundled, in every project"): agrees with PLANNER.md §2's lead
  bullet and with the crafter, whose `--bundle` mode treats an absent
  `--checkpoint` as `members.checkpoint: null` and says so in its log
  line. Nothing in the bundle path needs a checkpoint.
- **B**: §20 and §20.1 both have headings, so both pointers resolve
  (`test_doc_crossrefs` sweeps them now that the sentence names a
  section; the old "per PLANNER.md" was invisible to it). The ratification
  clause matches §20.1's "the parent's ratification of the decomposition,
  before anything spawns, is the control."
- **D**: a straight deletion of the condition. True against §20's own
  first paragraph and META.

No cite-against-phrase conflict came up. The finding's line numbers
(566, 573, 1682, 445/446) matched the shipped tree, and every carrier
was found by its phrase, once.

## Decisions I made that you should ratify

1. **Two new TARBALL.md-side pins.** The brief says pins 7 and 9
   survive, and they do, byte-unchanged. But the constraint says both
   sides' extracts are updated, and the suite's docstring is blunt that
   a pin update "without its twin's is exactly the drift the pair
   contract forbids". So TARBALL.md gains a pin on its general statement
   (through "authors the split sessions' materials", which takes in "in
   every project" and the §20 pointer) and one on the worked-example
   sentence. These pin my authored wording, which PLANNER.md §4 warns
   against for checkpoints; I judged a sanctioned-pair pin to be a
   different animal, since its whole job is to make the next editor of
   one twin visit the other. If you'd rather they be narrower, the
   clause "is a role transition in every project" is the load-bearing
   part.
2. **A negative pin, `RetiredSplitConditions`.** Two tests: the three
   conditional openings stay absent from CLAUDE.md and PLANNER.md, and
   TARBALL.md §3.4's checkpoint paragraph carries neither the bundle
   sentence nor "role transition". The finding's §6 is the reason: the
   suite pinned carrier A *in its conditional form* and so held the
   misreading in place through one fix already. A positive pin can't see
   a condition come back in the sentence next to it. The suite goes from
   2 tests to 4; the three doc suites from 41 to 43.
3. **Where §3.4's general statement lives.** Its own bold-led paragraph,
   "**The split is a role transition.**", between "Split supersession"
   and "Checkpoint-configured projects". It ends on the moved pin-9
   sentence, so bundled delivery is stated next to the transition and
   ahead of anything about checkpoints. It also says, in one sentence,
   that the rescope command itself is unchanged (the bare line stays the
   offer's content; the bundle is how it travels), which is ruling Q2
   from TARBALL.md's end. The checkpoint paragraph now ends on pin 7's
   sentence.
4. **PLANNER.md §20, one clause past the brief.** Besides wording the
   materials list ("commands, briefs, and, in a checkpoint-configured
   project, checkpoints" — parallel to VERBATIM-B and to META), I opened
   the blindness sentence with "Where a child has a checkpoint,". Without
   it the paragraph asserts, in a project with no checkpoint, that a
   contract about checkpoints "is met". I also turned "under META's
   grant, because it never builds…" into "under META's grant, which
   reaches the checkpoints because it never builds…", since the *because*
   only ever justified the checkpoints.
5. **Rider two went to §3, not §6.** It is a rule about a brief's layout,
   and §3 is where PLANNER.md's INDEX sends whoever is authoring a brief.
   Said generically: "the operator's ratified order of upcoming work",
   "a later heading". The reason given is tied to §2's
   transported-decisions rule rather than to any desk's history.
6. **Rider one's three facts, verified this session against shipped
   bytes**, since it lands in a global doc: TARBALL.md §7.5 gives 2 to
   "the script itself errored"; `bin/bale_open.py` refuses the whole open
   on a dry-run exit outside 0/1 as a defective oracle, before any
   session state exists; `bin/bale_report.py`'s hold judge counts a
   checkpoint exit 2 as the checkpoint holding ("the planner's artifact
   broke, which is the fixture side"). The bullet cites only TARBALL.md
   and bale's verbs. One thing I noticed and did not act on: §7.5 is
   written about `validation.sh`; `bale_open.py` applies the same table
   to the checkpoint script by comment. The bullet says what the rider
   said, and the docs do not contradict it, but §7.5 never says in so
   many words that it governs the checkpoint too. See Proposals.
7. **The exec bit.** `tests/test_sanctioned_pairs.py` arrived mode 755 in
   the request. The overlay can't be trusted to carry mode (TARBALL.md
   §5.1.1), so `apply.sh` has one `chmod +x` line and `validation.sh`
   asserts it, both from the crafter's one `--executable` list. If the
   file is *not* executable in the repo and the tarball's mode was an
   artifact of packing, that line is a mode change you did not ask for:
   drop it.

## Where to look closely

- TARBALL.md §3.4's new paragraph is the only substantial authored prose.
  Read it as a worker in a project with no checkpoint would: the first
  thing it meets after "role transition" is "in every project".
- CLAUDE.md §11.2 still opens "It stays in conversational mode and
  returns, in chat:". With the bundle as the delivery in every project,
  what comes back is chat plus a bundle file beside a `bale open` line.
  I left it: the rulings kept the offer model, §3 already says files can
  ride any shape, and the sentence is outside the carriers. If it reads
  wrong to you now, it is one clause.

## validation.sh: three checks that pass on the unmodified tree too

I ran the script against a staging copy with the change applied (all
pass) and against the unmodified tree. Five checks fail there, as they
should. Three pass on both, deliberately:

- *invariants* is a guard, not a change test: every heading and every
  numbered-item opener hashes to the base's value, which is the
  "nothing renumbered" constraint. Its bumpless and in-forecast halves
  read `.bale-manifest.json` and print a note when it is absent.
- *doc suites* passes on the old tree because the old tree runs the old
  test file. The new test file against the old docs fails in 8 places;
  I ran that separately.
- *exec bit*: the base file already had it.

The pinned strings inside `validation.sh` were lifted from the brief's
fenced blocks by a generator, not typed, and every comparison is on
bytes inside Python (whitespace-collapsed, the brief's own rule). No
comparison goes through `$(...)`.

## What I did not check

- The blind checkpoint, by construction.
- The full suite *in your tree*. In mine it ran 1426 tests: 1421 pass or
  skip, 5 do not, and all 5 are my sandbox (three in
  `test_include_group` want `bale.toml`, two in `test_changelog_record`
  want `claude/changelog/0.4.40.json`; neither shipped). They fail
  identically on the unmodified tree.
- Whether `docs/DOCS.md` §9 needs an edit. I read it: it names the pair
  generically ("rescope-offer prose with … pack-flag surface") and still
  fits. No proposal.
- `model_identity` in the feedback block: I can't see my own model
  string, and said so there rather than guess.

## Proposals

1. **Say once, in TARBALL.md, that §7.5's exit codes bind the checkpoint
   script too.**
   - What: one sentence in §7's blind-checkpoint paragraph or in §7.5.
   - Why: `bin/bale_open.py` and the hold judge both treat the
     checkpoint's 0/1/2 as §7.5's table, and PLANNER.md §4's new bullet
     now leans on that reading, but §7.5 as written is about
     `validation.sh` alone. A planner following the pointer lands on a
     section that doesn't mention their script.
   - Scope hints: `docs/TARBALL.md` §7 or §7.5, one sentence; no pair
     involved.
2. **Pin the riders' required phrases, if the desk wants them held.**
   - What: `exits 2` in PLANNER.md §4 and `sitting record` in §3 have no
     suite pin; only this response's `validation.sh` asserts them.
   - Why: `test_doc_crossrefs.py` is where single-doc content pins live,
     and it was out of this forecast. Authored wording around a required
     spelling usually gets no pin there, so this may be a deliberate
     no.
   - Scope hints: `tests/test_doc_crossrefs.py`, two constants.
