# notes — 2026-09-19-board-110-held-admissions-007

## Out-of-forecast paths (admit at apply)

Two `changes[]` paths sit outside the write forecast. Both are also
recorded in `feedback.self_reported.forecast_departures`.

- **`tests/test_pack_guards.py`** (modified) — rider 2's pin.
  `test_baleignore_negation_refusal_names_the_file` asserted the stale
  text verbatim (`MATCHER_NEGATION_SENTENCE + " at v0.1."`). Dropping
  the marker from `bin/bale` fails that assertion unless it changes too.
  - The edit is six lines. It now asserts the sentence ends at
    `supported. Offending line:` and that `at v0.1` is absent.
  - Neither the sibling's four suites nor `out_of_scope` names this file.
- **`tests/test_cli_help.py`** (created) — rider 6's destination, which
  the brief names. It is new, so the forecast could not list it.

Paste line with both admissions:
`bale apply <tarball> --allow-out-of-scope tests/test_pack_guards.py --allow-out-of-scope tests/test_cli_help.py`

## Where the admissions live: a stamp, not telemetry

I chose a new stamp, `.bale/sessions/<sid>/held_admissions`, written
beside `held_tarball`. It is a one-object JSON file: `version: 1` plus
the five admissions, under exactly the `readmissions` keys the composer
already takes. I chose it over the HOLD attempt's telemetry entry for
three reasons:

1. **Lifecycle for free.** It is written at the same terminal action as
   `held_tarball` and wiped by the same `_discard_hold_state` at the
   start of every retry. So "the latest held attempt's admissions"
   (your item 6) holds by construction; there is no attempt-picking
   logic that could pick the wrong one. The double-HOLD E2E pins it.
2. **It records the card's exact inputs.** Telemetry records
   `sandbox_off_source`, not "was `--no-sandbox` typed". It has no field
   for the card's `accept_checkpoint_change` predicate either
   (`checkpoint ran and stamp_matched is False`). Reading telemetry
   would mean re-deriving the card's logic in a second place, which is
   exactly the kind of copy 106 retired.
3. **47a's rule applies unchanged.** The card's fixture rung composes
   from the stamp's *outcome*, never the in-process dict, so the card
   and the amend report cannot disagree. If the stamp write fails, the
   card says so on the same line the amend report would print.

The stamp is always written, even when no admission was exercised. That
way an absent stamp means one thing: held before 0.4.37, or never held.

## Rulings I'd like ratified (judgment calls, flagged)

- **The base rung stays in-process.** It appears only on the card, and
  its behavior today is correct. So a failed admissions-stamp write
  degrades only the fixture rung; the base rung still carries the
  admissions. The E2E for a failed write pins both halves.
- **Note order.** The admissions note sits above the path note, and the
  command stays last. A report whose tarball path degrades therefore
  still has the path note as its second-to-last line, which kept the
  existing legacy-degrade pins meaningful.
- **Item 7's desk ruling is shipped as stated.** When there is no
  record, or an unreadable one, the successor still prints. It carries
  `--accept-checkpoint-change --sid <sid>`, preceded by one note naming
  the reason and listing which flags to re-state by hand. I saw nothing
  in the code arguing against it.
- **The parser is strict.** Wrong version, missing key, wrong type, or
  unknown keys all refuse the whole stamp, with a reason. Re-stating
  half the admissions would reproduce the original silent failure.
- **One pure-call default.** Calling `compose_hold_successors` without
  `held_admissions` / `held_admissions_why` re-states nothing. That
  keeps every existing unit caller byte-identical. Both production
  callers always pass one or the other, and the docstring says so.

## What the E2E proves

`HeldAdmissionsE2ETest` is your reproduction, driven through the real
CLI. It packs a session forecasting `hello.txt` with a failing oracle.
The response also creates `extra dir/new file.txt` and is applied with
`--allow-out-of-scope` for it, which HOLDs. Then:

- The card's fixture rung equals amend-checkpoint's last line, compared
  byte for byte.
- The line re-states `--allow-out-of-scope 'extra dir/new file.txt'`.
- `shlex.split`-ing that line and running it lands the tarball: exit 0,
  `[PASS]`, an `applied/<sid>` tag, the new file present.

A sibling test runs the pre-0.4.37 bare line on the same state and pins
it REJECTED, naming the path. That shows the landing test isn't passing
vacuously.

## Riders

1. **Twin checks retired, both.** Same proof as 47b's for `cmd_apply`.
   With a verb, `resolve_inbound_path` returns only from its last line,
   after both refusal branches. Both branches end in `fail_not_found` →
   `fail()` → `sys.exit`. The proofs are left as comments at both call
   sites. I also trued the two docstrings (`resolve_inbound_path`,
   `fail_not_found`) that still described the checks as live.
2. **"at v0.1" removed.** Its pin is the out-of-forecast edit above.
3. **run_hook's three f-strings** are verified and fixed. They were
   exactly the three `print(f"...")` lines, and output is unchanged.
   Pyflakes on `bin/bale` loses exactly those three warnings, and no
   file gains a new warning.
4. **`ComposeRetrySuccessorUnitTest`** is in `test_amend_checkpoint.py`,
   loaded via `_load_cli()`. `compose_retry_successor` is within the
   loader's reach limit: its call path is the two stamp readers,
   bin/bale's `log()`, and bale_report's pure composer. None of those
   reach back into `__main__`. The stamps are written with the writer's
   own serializer, so no git is needed.
5. **The `test_apply_preflight` docstring** now says row 32's test is
   its first pin and that session 1 deliberately pinned nothing.
6. **Done, not dropped.** `SubcommandHelpLayoutTest` moved whole to
   `tests/test_cli_help.py`: same four tests, same names. The budget was
   fine. `validation.sh` asserts the move at the AST level.

## Version and validation

- `bin/VERSION` is 0.4.37, with `claude/changelog/0.4.37.json`.
- `validation.sh` states the version invariant relative to the response.
  `bin/VERSION` must name a record whose `session_id` is this response's
  and whose version is newer than every other record's.
- One-apply-behind: the landing apply runs 0.4.36, so a HOLD during
  that apply writes no admissions stamp. Amend-checkpoint would then
  print the degrade line, which is the named-absence path working as
  designed.
- `validation.sh` gates the full suite behind `--slow`. I observed it
  passing on these exact bytes in a staging-shaped rehearsal: 1345 tests.
- My first rehearsal caught a bug in my own f-string check. It flagged
  format specs like `{n:03d}` as placeholder-less. The fixed check
  passes on the new tree and catches exactly the three `run_hook` lines
  on the request's base.
- Baseline: `test_include_group` and `test_changelog_record` were green
  on the request tree, so there was no packing defect there.
- The install's own `validate.sh` fails one check in this tree,
  `README.md present`. The repo-root README didn't ship in the request.
  That is unrelated to this change, and I didn't use that script.

## Proposals

- **What:** PLANNER.md §5 step 5 could say the retry re-states the held
  apply's admissions, and that the line bale prints already carries
  them.
  **Why:** the step reads as if `--accept-checkpoint-change` is the only
  flag the retry needs. That was the operator-facing gap this board
  closed in code. The sentence isn't wrong, just silent. `docs/` is out
  of scope here, hence a proposal.
  **Scope hints:** `docs/PLANNER.md` §5 step 5 only; one clause.
- **What:** add the admissions to the planner relay block beside
  `held tarball:`.
  **Why:** the desk rules on a fixture defect without seeing that the
  held apply needed `--allow-out-of-scope`, and that is context the
  desk might weigh. Out of this goal, and small.
  **Scope hints:** `bin/bale_report.py` `format_hold_relay_planner`;
  its unit pins in `tests/test_apply_preflight.py` `HoldRelayUnitTest`.
