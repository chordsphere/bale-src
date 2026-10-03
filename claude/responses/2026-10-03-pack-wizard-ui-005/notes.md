# Notes — 2026-10-03-pack-wizard-ui-005

The goal-less pack wizard now draws through `bale_wizard`, and I didn't
have to change a single answer stream or marker in the eight forecast
suites. All eight pass as shipped, and I left them byte-identical. The
full discovery run gives 1694 tests with the same six failures as the
unmodified tree (changelog records, ADR 0013, the include-group pulls).
All six come from repo files this request doesn't carry.

## What the walk looks like now

A title screen ("bale pack — interactive mode") shows the repo and a
"given" row listing the flags the command line already answered, so the
reader can see why a question was skipped. After it come three ruled
sections (Session, Scope, Brief). Each question is an item headed
`n/N  <key>`, and the key is the CLI spelling that answers it: `goal`,
`--slug`, `shape`, `--write`, `--checkpoint-file`, `--exclude`,
`--constraint`, `--out-of-scope`, `readme`. Each item has a short summary,
state rows where there is state to show, `!` warnings on a reject, and a
prompt that says what Enter does (`Enter = mixed > `,
`Enter = the includes > `, `Enter = none > ` then `Enter = done > ` on
lists, and so on).

## Decisions to ratify

- **PackWalk, not `bale_wizard.Walk`.** Walk numbers items against a
  fixed order. This walk is partly conditional: a read-only shape answer
  drops the forecast and checkpoint questions. `plan_pack_walk` plans the
  items up front from the same skip rules the helpers use, and `drop`
  removes those two items when the shape answer is read-only. So a
  `{sid}` project shows 1/9, 2/9, 3/9 and then 4/7 through 7/7. The count
  always matches the questions actually left. I also kept Walk's
  `[section]` headings out, because that is bale.toml table syntax. The
  headers still match `ITEM_HEADER_RE`.
- **Outcome 3 by holding, not by moving each gate's logging.** Between
  the walk's list questions and its README question, cmd_pack runs these,
  and all of them log:
  - the deferred blindness gate and the disjointness gate, which
    `bale handoff` shares;
  - on a read-only pack, the sweep, whose `close_session_with_record` in
    bin/bale logs too.

  `WalkLogHold` rebinds `__main__.log` and `__main__.fail` from the walk's
  first question until the README is resolved. A held line is replayed
  through the real `log()` with its `force` flag, so its text, its
  journaling, and its FORCE queueing are unchanged. Only when it prints
  moves. `fail()` releases the held lines first, so a refusal still reads
  its context lines before its error. `atexit` is a backstop. This is the
  same kind of reach-in `_pending_force_line_count` already makes.
  **Look closely here.** The native home for a hold is bin/bale's `log()`
  (see Proposals). I stayed inside bale_pack because bin/bale is outside
  every forecast I could see.
- **The README question keeps `confirm_yn`'s exact answer set.** y or yes
  (any case) accepts. Anything else declines without re-asking, and EOF or
  ^C declines rather than aborting. The brief says "EOF and ^C still abort
  the pack", but at the README prompt they never did, and outcome 1 pins
  today's meaning. This is also why the item calls `ui.ask` and not the
  layer's `confirm`: `confirm` re-asks on "x", which today means no.
- **No `?` help on walk prompts.** `?` is a valid goal, slug, pattern, or
  list item today, so consuming it would change what the answer means.

## Helpfulness review (outcome 6)

- **Slug: Enter now takes a slug derived from the goal.** It used to
  re-prompt "(cannot be empty)". The rule is the first four non-stopword
  words, with hyphenated words kept whole, capped at 40 characters. If
  the goal has no ASCII letters or digits, Enter re-prompts as before. A
  script that typed Enter at the slug to *test* the re-prompt would now
  shift by one answer. The brief sanctions this, and no suite did it.
- **Slug: the answer echoes its session id** (`Session id:
  2026-10-03-…-001`, using `peek_session_id`).
- **Forecast: the screen shows what Enter resolves to**, the resolved
  include set ("`.` (the whole tree)" on a bare pack).
- **Checkpoint: the screen shows the resolved per-session path for this
  pack's sid and whether HEAD already has it.** So it says before you
  press Enter whether Enter will pass or whether the pre-flight will
  refuse. I considered making Enter pick candidate [1] when nothing is
  committed (that Enter refuses today, so the letter of outcome 1 allows
  it) and rejected it. It would commit an oracle the operator never
  chose, and any stray `.sh` in cwd qualifies. Enter still means none.
- **Excludes: `.baleignore` state is shown as a state row.** It reads
  none, its patterns, or present-but-empty, and the old 212-column
  paragraph is gone.
- **Work class: the letters are rows with Enter's answer marked.** The
  summary says the kind is stamped as the work class and that `r` locks
  nothing.

## Forecast departures (admit at apply)

- `tests/test_pack_wizard_ui.py` (new). This is the pack-wizard suite the
  brief invites:
  - `suggest_slug`;
  - PackWalk numbering and headings;
  - answer meanings fed in-process (shape letters and spellings, the
    README set, the slug default);
  - WalkLogHold mechanics;
  - pty runs that type each answer once its prompt appears, so the echo
    lands where a user sees it, and assert outcomes 2 and 3 over the walk
    span.

  It is outside session C's files.
- `tests/test_upgrade_required_members.py` (new). Tests ship with code.
  This suite derives bin/bale's load-time import closure from the sources
  (AST, module scope, module-scope `try` bodies) and pins
  `REQUIRED_RELEASE_MEMBERS` against it. That keeps the next load-time
  sibling from drifting the way four did. It doesn't belong in the
  pack-wizard suite.

## upgrade.sh rider

I added `bin/bale_stats.py`, `bin/bale_open.py`, `bin/bale_relay.py`, and
`bin/bale_wizard.py`. **I also added `bin/VERSION`, which the brief didn't
list.** bin/bale reads it at load and `sys.exit`s without it, which meets
the array's own criterion. `bin/bale_sandbox.py` stays off. Every importer
loads it lazily inside the functions that confine (apply/retry staging and
open's dry run), so every verb still loads without it, and install.sh's
post-swap layout check names the gap. The comment records this, and the
new suite pins sandbox as the deliberate exception. build.sh's subset
assertion still holds, because all five are in RELEASE_FILES.

## Smaller things worth knowing

- `plan_pack_walk` reads the merged config before the title, because the
  checkpoint item exists only for a `{sid}` base. A malformed bale.toml
  now refuses before the first question instead of at the checkpoint
  question.
- `format_checkpoint_candidates` gained `indent=` (default 2, which is
  the old output). The walk passes the item body indent. Its format is
  pinned by test_checkpoint_file_flag and is otherwise unchanged.
- `_wizard_input_list` stays as it was for its two callers outside the
  walk: the soft-cap `[e]` step of `bale pack` and of `bale pack
  --context`. `_wizard_input_required` is gone; the walk was its only
  caller.
- `model_identity` is the session's configured identifier
  (`anthropic:claude-opus-5-5`). The serving model can differ from the
  configured one, and nothing attests it.
- validation.sh took 99 s here. `--slow` opens the suites' gated cases.

## Proposals

- **A native log hold in bin/bale.**
  - *What:* add a hold to bin/bale's logging section, for example a
    module-level buffer that `log()` appends to and `fail()` drains first,
    exposed as a context manager. Then retire WalkLogHold's
    `__main__.log`/`fail` rebinding.
  - *Why:* the rebinding works and is tested, but it only catches callers
    that import `log` lazily at call time, and it is the second bale_pack
    reach into `__main__` state.
  - *Scope:* bin/bale section 2 plus bale_pack's cmd_pack (about 10
    lines).
- **Restyle the read-only sweep prompt.**
  - *What:* bring the sweep's y/N onto the layer, or at least wrap it to
    80 columns.
  - *Why:* it is out of scope by the operator's reading, but it is the
    one line inside the walk span over 80 columns (about 200) on a
    read-only pack with a sweepable session. My pty test excludes it by
    marker.
  - *Scope:* `bale_wizard.confirm` re-asks on unknown answers, where
    `confirm_yn_decision` declines. That is a meaning change, so it needs
    the operator's ruling.
- **Additions to bale_wizard, for session C or a follow-up (additive).**
  - *What:* a `choice` primitive (lettered or numbered rows, Enter's row
    marked, raw answer returned), which the shape and checkpoint items
    hand-build today from `state` + `ask`. And a `Walk` option for a
    shrinkable plan with plain-word headings, so PackWalk could become a
    Walk configuration.
  - *Why:* the docstring's "Extension points" already anticipates the
    first.
- **BALE.md §7.3 sentences for the 99b true-up.** For example:
  - "The goal-less wizard draws through the shared wizard layer
    (`bale_wizard`): one item per question, headed by the flag that
    answers it, with the count re-derived when a read-only answer drops
    the forecast and checkpoint questions."
  - "Enter at the slug question takes a slug derived from the goal."
  - "`[bale]` log lines from the post-walk gates print after the README
    question."
- **The pre-walk `[bale]` lines** (the tree position, and the 187-column
  "argv-only pack gates passed" line) were left as they are; outcome 3
  left them to my judgment. They are pack logging before the walk.
  Wrapping them is a bin/bale `log()` question for every verb, not a
  wizard one.
