# Notes — 2026-09-16-board-99a-outward-docs-003

## Correction — why the first attempt HOLDed (`corrects` is set)

The first attempt HOLDed on my own `validation.sh`, not on the work. The
blind checkpoint passed 5/5, and eight of my nine checks passed on the
real staging tree.

- **The failed check:** `bin/VERSION untouched (bumpless)` asserted the
  literal `0.4.33`, which I read off the request's copy of the tree.
- **What staging carried:** apply staged with `target-base` from main's
  tip `1f25d17`, where the wave's bumper (`board-47a-hold-card-triage`)
  had already landed `0.4.34`. The brief said exactly this — "bumpless
  under 0.4.34" — and I tested a version number instead of the rule.
- **The fix:** the check now asserts what bumpless means: the response
  declares no `changes[]` entry for `bin/VERSION`. An `apply.sh` that
  touched the file undeclared fails bale's reconciliation before
  `validation.sh` runs, so the manifest is the whole surface. The staged
  version is still printed, for the log only.
- **Rehearsed:** passes with a staged `0.4.34` and with `0.4.33`, and
  fails when a manifest declares `bin/VERSION`. The full script re-ran
  9/9 with every claim agreeing on a staging copy carrying `0.4.34`.
- **What changed, and what didn't:** only `validation.sh` and the
  manifest's `corrects` and feedback fields changed. Nothing under
  `files/` changed — the same four files, byte for byte — so the
  checkpoint's 5/5 PASS still describes these bytes.

The check label is unchanged, so `claims` and `validation_will_run` still
pair verbatim. The lesson, which I applied to the rest of the script: an
invariant under `target-base` staging has to be stated relative to the
response, never as a literal copied from the request tree. The other
checks already were — the flag fingerprint covers `bin/bale`, which the
base-drift gate protects, and the README checks glob the staged tree.

**At retry:** `tests/test_probe_clipboard_config.py` needs admitting
again. Out-of-forecast admissions are per invocation and never carried
forward from the held attempt; the TTY prompt offers it, as it did the
first time.

**Seen in the HOLD card:** board-47a's triage has landed. The card now
carries `judge:`, `failed probes:`, and a next step keyed to the desk's
ruling. The README's HOLD paragraph and `bale apply --help` still
describe it truly — diff hint, log, preserved staging, `bale retry` /
`bale revert` — but neither mentions the ruling-keyed next step. I have
not read 47a's `bin/bale_apply.py`, so I did not reword against a card I
have only seen once. Proposal 6 below.

## Light question block — the trail (TARBALL.md §5.10)

I ended the first turn on a three-question light block after reading and
before building. The packer answered all three "as assumed", with riders:

- **[1] Walk `[probe] clipboard_command` at the project layer only?**
  As assumed, with the reason stated in the wizard prompt itself. The
  prompt now says the crafter reads the project bale.toml as shipped in
  the request, so a global value would never reach the probe epilogue.
  The global wizard neither walks nor inherits the key. The same reason
  is written on `PROBE_VALUES` and on the `merged_config` branch.
- **[2] New suite `tests/test_probe_clipboard_config.py`?**
  As assumed. It is enumerated below for admission.
- **[3] README says BALE.md lives in the source repo, not the install?**
  As assumed. Install readers are pointed at `bale help <command>`, and
  BALE.md is named as the source-repo tool doc. Whether the release
  should ship BALE.md is a Proposal below, not a change here.

## Outside the write forecast — admit per path

- **`tests/test_probe_clipboard_config.py`** (created). The goal's config
  key needs tests, and none of the five forecast test files is about
  probes. A dedicated suite also gives the bale↔crafter agreement tests
  a natural home. This was ratified in answer [2].

None of the five forecast test files changed. The wizard pins they
carry still pass untouched, including the global wizard's
`sandbox.enabled` absence check. The walk's prompt count also stays
well under the suites' `"\n" * 40` answer budget.

## Judgment calls worth a look

- **The accessor refuses crafter-unreadable values loudly.** It does not
  return None for them. The crafter's reader is a minimal scan: it treats
  any backslash as unset, stops at an embedded double quote, and reads one
  line. The renderer's `json.dumps` turns control characters into
  backslash escapes. So those values would parse fine in bale and then
  vanish at craft time — bale and the crafter disagreeing about whether
  the opt-in is configured.
  - `probe_clipboard_command_problem` names the reason.
  - `get_probe_clipboard_command` calls `fail()` on it.
  - The wizard rejects the entry and keeps the current value, the same
    posture `staging.strategy` takes.
  - `CrafterAgreementTest` shows each refused value really would read as
    unset crafter-side, so the refusal is doing work.
- **`ensure_ascii=False` for `[probe]` only.** With the default,
  `tee /tmp/probé.txt` renders as `\u00e9`, which the crafter reads as
  unset. The other sections keep their existing serializer byte for byte.
- **Two small code touches inside the "strings only" lane.**
  `_prompt_value` and `_prompt_path_list` gained a defaulted
  `unset_effective` keyword, following the existing `_prompt_bool`
  precedent. Without it, every string key's effective line read
  "(no hook will run)" and every list key's read "(no extra search
  paths)", which was wrong for archive_dir, packer, validation.base,
  include_group, and the rest.
  - The defaults keep the hook and search_paths wording exactly.
  - It changes display text only; no value, prompt order, or return path
    changed.
  - The generic suppress lines ("no hook runs at this layer") now read
    true for any key.
- **`bin/bale` flag surface: proven unchanged, not just claimed.**
  `validation.sh` hashes every subparser's actions and set_defaults. The
  expected value comes from the request's base bytes, and the check was
  rehearsed to move under a changed default and a renamed flag. Two
  parser *comments* also changed: the handoff comment had drifted above
  `open`, and the config comment still claimed `init` was the only
  subcommand.
- **Open-help ordering follows `bale_open.cmd_open`'s docstring.** Argv
  parse and the argv-level gates come first, then the missing-base refusal
  before the dry-run, then the replay. The help also says the early gates
  are a cost ordering, not a substitute; that is the docstring's phrase.
- **README HOLD wording stays at what the card offers today.** That means
  the diff hint, the preserved staging, the log, and the retry/revert
  lines. `board-47a-hold-card-triage` is reworking the card this wave, so
  I described outcomes, not the card's layout.
- **README length is ~11.7 KB, not the old 8 KB.** The brief's ten daily
  flows each got a real command line plus two to four sentences. I cut
  the three-way upgrade comparison to two sentences, and the README
  carries no date.

## Known divergence, not fixable in this lane

A hand-edited TOML **literal** string, `clipboard_command = 'pbcopy'`,
parses fine in bale: the accessor returns `pbcopy`. The crafter's scan
only reads double-quoted values, so it reports "treated as unset". The
wizard always writes double quotes, so one `bale config init` re-run
normalizes the file. `tools/craft_response.py` is board-96's path this
wave. Proposal 3 below.

## Review hints

- The retry description's two-rulings paragraph. I condensed PLANNER.md
  §5 step 3's fork into two sentences; check the wording matches desk
  usage.
- README "Retry a HOLD, or amend the checkpoint" says the same thing for
  install readers.
- I read every help string in `build_parser`. I did not verify every
  `BALE.md §N` citation inside per-flag help against 99b's coming
  true-up. The section headings they cite all still exist.
  - One soft spot: `handoff`'s description cites TARBALL.md §5.6.3,
    which is now a one-line "moved" pointer. It still resolves, so I
    left it.

## Validation

`validation.sh` was rehearsed in a simulated staging tree: base tree,
`files/` overlay with the mode stripped, `apply.sh`, then the script. All
nine checks passed and every claim agreed, in about 54 s; the claims are
marked `observed`. The same script run against the unedited base FAILs
help, wizard, README, and the new suite, and PASSes the two invariants,
so the needles are live.

The rehearsal ran unconfined here. Under apply it runs in the sandbox
with network off. Nothing in it needs network; PTY-free piped wizard runs
and unittest are all local. The full suite (1087 tests) also passed on
the edited tree before packaging, as did the install's `validate.sh`
(89 checks).

## Proposals

### 1. Decide whether the release ships BALE.md
- **What:** decide whether the release tarball carries `BALE.md`.
  Ship it, or keep excluding it and say so where users look.
- **Why:** the README now points install readers at `bale help <command>`
  because `scripts/build.sh` excludes BALE.md (source-only extras, per
  BALE.md §13 v0.0.1). Several `--help` strings still cite
  `BALE.md §N`, which an install reader cannot open.
- **Scope hints:** `scripts/build.sh` release list, `install.sh`
  INSTALL_LAYOUT, `validate.sh` layout rows,
  `tests/test_release_packaging.py`. If kept source-only, a later
  `bin/bale` string pass could qualify the citations.

### 2. BALE.md learns the new key and the trued help
- **What:** BALE.md's configurables surface (§3.6 and the `bale.toml`
  sections) names `[probe] clipboard_command`, project-layer only, with
  its reason. The command sections pick up open's board-68 order and
  retry's two rulings.
- **Why:** this session landed both in code, but BALE.md is board-47a's
  path this wave. BALE.md §3.6 is the discoverable-surface contract the
  wizard tests cite.
- **Scope hints:** BALE.md only; natural rider for 99b's true-up.
  Ordering: after this response and 47a land.

### 3. Crafter reads TOML literal strings, or refuses them loudly
- **What:** have `read_clipboard_command` accept a single-quoted TOML
  literal string. At minimum, its "treated as unset" note should name the
  single-quote case.
- **Why:** it is the one shape where bale's accessor and the crafter
  still disagree (see "Known divergence"). `CrafterAgreementTest` in the
  new suite is where a pin would go.
- **Scope hints:** `tools/craft_response.py` (board-96's lane this wave),
  `tests/test_craft_response.py`, and one case added to
  `tests/test_probe_clipboard_config.py`.

### 4. A production reader for the accessor
- **What:** give `get_probe_clipboard_command` a bale-side caller, most
  likely a `bale status` config row reading "probe clipboard: <cmd> /
  unset".
- **Why:** today its only consumer is the standalone crafter, so the
  accessor's loud refusal fires only in tests. A status row would surface
  a crafter-unreadable hand edit before a probe silently falls back to
  remedy text.
- **Scope hints:** `bin/bale` `cmd_status` / `bin/bale_report.py` status
  formatter, plus a status test; a behavior change, so not this lane.

### 5. Preserve paragraph and example layout in help descriptions
- **What:** render help descriptions with argparse's
  `RawDescriptionHelpFormatter`, or an equivalent that keeps explicit
  `\n\n` breaks.
- **Why:** argparse's default formatter collapses the explicit breaks the
  descriptions already carry.
  - `bale completion --help` flattens its indented
    `source <(bale completion bash)` examples into the running
    paragraph.
  - apply and retry lose their paragraph breaks, which this session's
    additions make longer.
  - This is a rendering change, so it was out of scope for a strings
    lane.
- **Scope hints:** `bin/bale` `build_parser` (formatter_class on the
  subparsers). The completion generator walks actions, not descriptions,
  so it is unaffected. The needles in this response's `validation.sh`
  already run with `COLUMNS` unwrapped.

### 6. Re-true the HOLD wording against 47a's landed card
- **What:** re-read the README's "Apply a response" HOLD paragraph and
  `bale apply --help`'s HOLD sentence against the card
  `board-47a-hold-card-triage` landed. If the ruling-keyed next step is
  now the card's main affordance, name it.
- **Why:** this session's HOLD showed the new card (`judge:`,
  `failed probes:`, "Next step, by the desk's ruling"). Both texts here
  were written before it landed. They are still true, but they describe
  a retry/revert pair rather than the ruling fork the card now leads
  with.
- **Scope hints:** `README.md` and `bin/bale` (apply and retry
  descriptions), read against `bin/bale_apply.py` / `bin/bale_report.py`
  as landed. Only after this response and 47a are both on main.
