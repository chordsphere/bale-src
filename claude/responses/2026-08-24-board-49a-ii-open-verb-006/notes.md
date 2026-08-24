# notes.md — 2026-08-24-board-49a-ii-open-verb-006

The verb landed clean: 18 new tests, the full 535-test suite green,
and two live smoke runs (brief-only and full-checkpoint bundles)
through the real pipeline, confined. Everything below is either a
judgment call you should ratify or a pointer for review. All five
`changes[]` paths sit inside the stamped forecast (`BALE.md`, `bin`,
`tests`) — no drift to admit.

## The row-48 decision (yours to ratify)

**No standalone dry-run echo on the non-bundle pack path.** The
dry-run leg is `bale open`-only. Three reasons, in weight order:

1. The hazard the proof guards is the paste surface: an operator
   pasting a desk-emitted line over members they never inspected.
   On the typed path the planner authored the checkpoint, committed
   it (or hands it via `--checkpoint-file`), and can execute it
   directly at the desk — there is no blind hop for the proof to
   close.
2. Pack today executes no project scripts; adding an execution step
   to every scoped pack changes its cost profile and its character,
   and would need its own sandbox/no-sandbox surface on a command
   that never had one.
3. Single-homing: the proof's semantics (exit-code judgment, the
   vacuous-oracle warning) live in one place, `bale_open.py`, with
   one test surface.

The disposition is recorded in BALE.md §6.7's trued-up prose. If you
ratify the opposite, the seam is clean: `dry_run_checkpoint` takes
script bytes and is caller-agnostic — a pack-side caller would reuse
it as-is.

## Dry-run exit-code judgments (ratify)

The ratified row names only exit 2 as a refusal. I filled in the
rest of the space:

- **Exit 1** — the expected-HOLD proof: probe-verdict lines echoed,
  a proof line printed, proceed.
- **Exit 0** — proceed with a loud `WARNING … vacuous` line. A
  checkpoint that passes against the unmodified base cannot
  distinguish landed from not-landed, but an invariant-only
  checkpoint (regression guards) is a coherent planner choice, and
  the row ratifies no refusal here. If you'd rather refuse, it's a
  three-line change and one test flip.
- **Any other code** (including the sandbox prologue's 97, which
  gets its own message when the sentinel is present) — refused as
  outside the probe contract's 0/1 verdicts: the oracle itself is
  defective, same class as exit 2.

## Other mechanism calls (flagged per the brief's latitude)

- **Flag surface**: positional bundle + `--verbose` + `--no-sandbox`
  only. The bundle argument resolves like apply's tarball argument
  (cwd, then `apply.search_paths`) via the shared resolver. No
  `--json` at v1 — deferred with a proposal below.
- **Read-only mechanics**: the dry-run copies the live working tree
  (`.git` included, `.bale/` excluded) into a scratch tempdir and
  runs there, confined by default. Read-only w.r.t. the real tree is
  therefore *structural* — it holds even under `--no-sandbox`, and a
  test pins it (a write-attempting checkpoint leaves the repo
  untouched). I chose the working tree, not the branch tip, as "the
  live base": it is what pack will ship, per the stale-queue rule.
- **Dry-run log**: `.bale/logs/open-<bundle-stem>.log` — pre-sid, so
  the session-log convention can't apply; the `open-` prefix keeps
  it distinguishable, and the proof survives the console.
- **Repo required**: `bale open` refuses outside a git repo rather
  than walking pack's git-init path — the dry-run needs a live base,
  and a bundle targets an existing project by construction.
- **Unconfigured-project pre-check**: a checkpoint-bearing bundle
  against a project with no `[validation]` base refuses *before* the
  dry-run — the same refusal the replayed `--checkpoint-file` would
  give, moved ahead of the dry-run's cost.
- **Sealed archive**: unknown members refuse (per §6.7's "grounds to
  refuse" — I made it a hard refusal, not discretion), as do
  declared-but-missing members, duplicates, and any non-flat or
  non-regular member. Extraction is via `extractfile` in memory, so
  no tar path quirk can write outside the process.
- **Version bump**: `bin/VERSION` 0.4.12 → 0.4.13 — a new
  user-facing verb. Flagging because the brief didn't name it; the
  one-line file exists for exactly this, and `bin/bale`'s new
  comments cite v0.4.13.

## Where to look on review

- `bin/bale_open.py` — all new logic lives here (~530 lines, four
  sections, indexed). The trust-order pipeline is `cmd_open`'s
  docstring; `read_bundle` is the gate.
- The `bin/bale` diff is small and mechanical: one import block, one
  subparser, `"open"` added to the injected-files pre-check tuple,
  one docstring sentence.
- `tests/test_open_verb.py::test_supersede_intent_accepts_under_piped_stdin`
  is the end-to-end the 49a-i transported decision named: piped
  stdin would decline the exchange; the bundle's intent supplies the
  accept, routed through `_resolve_supersession` unchanged, and the
  parent closes as superseded-by-split.

## Validation notes

- `validation.sh` runs the targeted tier by default (~45s) and gates
  the full 535-test discover behind `--slow` (it alone is ~100s,
  past the §7.6 target when stacked). Claims are annotated
  `observed` — I ran both tiers here before shipping.
- The repo's own `validate.sh` reports 5 pre-existing failures
  (`upgrade.sh` and the root `README.md` are not in the shipped
  context) — **identical counts (76/5) on the pristine shipped tree
  and on this change set**, so they are packing artifacts, not
  regressions. Your real tree, which has both files, should be
  unaffected.
- The confined-tier test is `skipUnless(userns)`; it ran (and
  passed) in this environment, and the `--no-sandbox` tier covers
  the verb's logic where userns is absent.

## Proposals

- **For 49b (crafter emission), two consumer facts to build
  against.** What: (1) `bale open` refuses any archive member the
  manifest doesn't declare and any declared member the archive
  doesn't carry — the emitter must write exactly
  {bundle.json} ∪ declared members, flat; (2) the emitted
  `bale open` line beside the bundle should carry the bundle
  filename only (the search-path resolution makes a downloads-dir
  save paste-ready). Why: both are behaviors this session fixed
  that only the emitter exercises from the producing side. Scope
  hints: the crafter tool; queued next in the bracket.
- **A `--json` report for `bale open`.** What: a one-line stable
  report (verified members, dry-run exit, proof summary, replayed
  sid) mirroring pack's `--json`. Why: the harness era will consume
  open programmatically, and today the machine-readable half exists
  only for the inner pack. Deferred (see manifest) rather than
  landed because the report contract is best designed against 49b's
  emitter, which fixes what the desk consumes. Only after 49b.
- **Watch item, standing**: the MASTER.md §3 unconsumed-intents
  watch re-triggers on the first live unconsumed intent observed
  after this lands. The loud-report path is implemented and tested
  (`test_unconsumed_intent_reports_loudly_and_packs`); the
  refuse-vs-proceed revisit is the desk's, on the live specimen.
