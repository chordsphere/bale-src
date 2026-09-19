# 2026-09-18-board-47b-relay-blocks-003 — notes

The blocks, the routing line, and the third ruling are all in. All four
riders landed too. The pre-flight check had room for them, so nothing
was dropped at the seam. Every changed path is inside the write
forecast. `claude/changelog/0.4.36.json` is covered by the
`claude/changelog` entry. There is nothing to admit at apply.

**One apply behind.** The apply that lands this session renders the
0.4.35 card and prints no relay blocks. The next HOLD or clean apply is
the first one to show them. 47a had the same property.

## What the operator sees

On a HOLD, two blocks print, then the card. Each block is bracketed by
the verbatim sentinels:

- `=== RELAY BEGIN <sid> to planner|worker ===`
- `=== RELAY END <sid> to planner|worker ===`

The blocks print in send order. Each opens with where to paste it, in
capitals, plus a line that is either "Send it now: it goes first." or
the WAIT line.

The card's trailer opens with the send-first line, then the three
forks. The send-first line reads `send first: planner — the checkpoint
held; the worker block waits for the planner's ruling`, or the worker
form.

On a clean apply, one planner block prints just above the `[PASS]`
banner. It carries:

- the verdict, in the walkthrough's vocabulary;
- the admissions, or `none`;
- `notes.md` verbatim, or "The response shipped no notes.md.", or why it
  could not be read.

`--json` is unchanged. The blocks go wherever the human lines go, which
json mode already routes to stderr. There is an end-to-end test that
stdout stays one parseable line.

## Decisions to ratify

1. **`send first:` is a trailer line, not an aligned row.** The card's
   rows pad every label to the longest one (`failed probes`). As a row
   it would render `send first:    planner`, which is not the verbatim
   bytes. The trailer is emitted verbatim, so the line reads exactly
   `send first: planner — …`, two-space indented like a row, just above
   "Next step". If you would rather have it among the rows and accept
   the padding, it is a three-line move in `format_hold_card`.

2. **The worker block never touches the log.** The log's worker band is
   not clean. bale journals `blind checkpoint exit code: 1
   (claude/checkpoints/<sid>.sh)` inside it, because apply's `log()`
   line lands after the `=== worker validation.sh ===` header. So the
   worker block takes the worker's `validation.sh` output from memory
   instead, meaning the same bytes the pipeline already holds for
   telemetry.
   - `format_hold_relay_worker` has no parameter for checkpoint output,
     bands, or the log. A unit test and a `validation.sh` assertion both
     pin that parameter set.
   - The failed labels come from the stamp's `failed_probes`. That is
     the same list the card and telemetry carry.
   - The planner block does inline the real log bands, `[bale]` lines
     and all, "as the log has them".

3. **Bands are cut by byte offset, not by searching the log.**
   `apply_pipeline` records the session log's size at three points:
   before the checkpoint, after it, and after `validation.sh`.
   - This scopes the bands to this attempt. A retry's planner block
     carries one checkpoint band, not two; an end-to-end test proves
     it.
   - Inside the checkpoint slice, the trailing
     `=== worker validation.sh ===` header is removed by an exact
     test on the final bytes. A checkpoint that prints that header
     mid-output cannot move the cut; a unit test covers this.
   - I left `bale_staging.py` unchanged, as the brief expected.

4. **Sentinel guard.** Any inlined line that starts with `=== RELAY `
   is indented two spaces. Worker or checkpoint output therefore cannot
   close a block early for a parser keyed on whole-line sentinels.

5. **The worker block's closing line.** It reads
   `bale retry '<held path>'`, always quoted (`_always_quoted`), and is
   preceded by a sentence telling a re-attempt to set
   `"corrects": "<sid>"`. When the held-tarball stamp failed, it says
   why and falls back to `'<response-tarball>'`.

## The base-defect ruling: what I found about flags

The brief asked which flags a retry onto a repaired base actually needs.

**Nothing about the repaired base itself needs a flag:**

- A repair packed while this session is open has to be
  forecast-disjoint from it, because of the open-session pack gate.
- The base-drift gate compares only `changes[]` paths against
  `base_files`.
- So the gate has nothing to refuse.
- `--accept-base-drift` on a repaired path would be actively wrong. It
  would land the held bytes over the repair.

**What the retry does need is every admission the held apply
exercised.** It is the same tarball, and no override carries forward
from a failed attempt; retry's own `--help` says so. The flags are:

- `--allow-out-of-scope` per admitted path (flag- or prompt-admitted);
- `--accept-base-drift` per path admitted at the held apply;
- `--allow-missing-required-check`;
- `--accept-checkpoint-change` when `stamp_matched` was false;
- `--no-sandbox` when it was typed. A config-disabled sandbox needs no
  flag.

The rung is `bale retry <held> [those] --sid <sid>`. `--sid` is vetting,
as on the fixture rung. It also makes the base line textually distinct
from the work-defect line. Without it the two are byte-identical, since
both use the held path and differ only in which bytes sit there.

The flag grammar is shared with `compose_admission_command` through the
new `_admission_flag_tokens`. The card keeps `shlex.quote` and the
refusal remedy keeps `_always_quoted`. The remedy's output is unchanged,
and a new unit test pins one case.

**Look closely here:** the fixture-defect retry rung has the same latent
gap. It retries the same bytes without re-stating admissions. I did not
change it. It must match `bale amend-checkpoint`'s report byte for byte,
and that report composes from the `held_tarball` stamp alone. See
Proposals.

## Riders

- **Walkthrough → `_checkpoint_attribution`.** Done, with a new
  `_worker_attribution` beside it. The exit-2 tail `; inspect the
  checkpoint script` is appended at the walkthrough's call site, so the
  output is byte-identical. I routed only the walkthrough, as the
  registry entry asked. The apply log line (`HOLD — blind checkpoint:
  PASS · …`) is a third wording I left alone: it is journaled, and
  nothing asked for it.
- **`compose_hold_successors` docstring.** Now says `compose_retry_successor`
  delegates to it and the degrade shape's one home is here.
- **`base_drift_overrides`.** Added to `format_session_dossier_json`'s
  attempts key list, in `_dossier_attempt`'s order.
- **`DOCS_READ_EMPTY_STUB`.** TARBALL.md §5.2.2 gains a sentence naming
  the warning, as the one exception to "honest empties".
- **The existence check at `cmd_apply` (~3757).** Proved unreachable and
  removed.
  - With a verb, `resolve_inbound_path` has two outcomes. It either
    returns a path that just passed `is_file()`, or it calls
    `fail_not_found`. That function ends in `fail()`, which always
    reaches `sys.exit`.
  - The only thing the check could catch was the file vanishing between
    those two lines. The removed code had its own message and no
    near-name listing, so it was the worse refusal anyway.
  - A comment at the site records the proof.

## Docs

- **`docs/TARBALL.md` §7** gains the worker-facing paragraph after the
  blind-checkpoint paragraph. The home is my choice; §7 is where the
  checkpoint is introduced to the worker. It covers the `RELAY … to
  worker` block, what is in it, "never asks for the session log", and
  the spec-from-labels ask. It cites only `PLANNER.md` §5. All four
  doc-pin suites pass unchanged, and no held pin moved.
- **`BALE.md` §8.8** documents the blocks, the send-first line, the
  base fork with its flag reasoning, and the clean-apply relay.

## Validation and staging

`validation.sh` was rehearsed against a staging that mirrors the target
base: the request's `context/` tree committed as HEAD, the `files/`
overlay, and `.bale-manifest.json` placed. Every claimed check passed,
in about 50 seconds.

The `--slow` whole-suite check fails in my mirror only on
`test_include_group`'s `TestThisRepoGroup`, which reads a repo-root
`bale.toml` that `context/` does not carry. Those same three errors
appear on the untouched base in my mirror, so it is a packing gap, not
a regression. On the real tree I expect `--slow` to pass. It is
unclaimed either way. The rest of the suite is 1273 tests, 26 of them
new, all passing.

## Proposals

- **Stamp the held apply's admissions at HOLD time.** Write them beside
  `held_tarball` (e.g. `.bale/sessions/<sid>/held_admissions`).
  - *Why:* the fixture-defect retry rung and `bale amend-checkpoint`'s
    report both retry the same bytes, but neither re-states the
    admissions, so a held apply that needed `--allow-out-of-scope`
    refuses at the fixture retry. The base rung only gets this right
    because the card renders in-process.
  - *Scope hints:* `bin/bale` (`compose_retry_successor`,
    `read_held_tarball_stamp`), `bin/bale_apply.py`'s inspect branch,
    `compose_hold_successors`' fixture fork. The card and amend report
    must change in one session to keep their byte agreement.
- **Retire `cmd_retry`'s twin existence check in `bin/bale`**, the one
  after `resolve_inbound_path(..., verb="retry")`.
  - *Why:* the proof above applies verbatim; its comment already says
    it is unreachable since 106.
  - *Scope hints:* `bin/bale` only. `handoff`'s check probably has the
    same shape.
- **Pin the TARBALL.md relay sentence** in `tests/test_sanctioned_pairs.py`
  or `tests/test_doc_crossrefs.py`.
  - *Why:* it states a worker-facing wire fact (the `to worker`
    sentinel) that the code pins but the doc does not.
  - *Scope hints:* board 109 holds both suites this wave, so this goes
    after it lands.
- **Include the repo-root `bale.toml` in future requests.**
  - *Why:* without it, `test_include_group` errors in any mirror a
    worker rehearses on, and a `--slow` run can't be rehearsed green.
