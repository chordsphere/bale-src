# notes.md — 2026-08-04-board-6-checkpoint-core-004

## Decisions to ratify

- **Dangling-refusal siting.** The brief says "loud refusal at apply
  pre-flight"; I sited the check right after the merged-config
  resolution in the apply pipeline (beside the staging-strategy
  resolution), because that is where `base_sha` is first in hand — the
  refusal needs the base tree to ask "committed there?". It is still
  pre-staging and pre-branch: no staging tree exists, no `bale/<sid>`
  ref exists, the session stays open, and the only disk effects are
  the session-dir stamps every apply writes. The test suite pins all
  of that. If you want it literally inside §8.1's numbered steps, it
  would need its own target-base resolution there — doable, but
  duplicative; say the word and a follow-up moves it.
- **The always-stamp invariant lives in the builder.**
  `build_telemetry_attempt` writes `attempts[].checkpoint` whenever
  `validation_state` is not None — the caller's object when given,
  else the known-zero `{"configured": false}` — and omits the key
  otherwise, regardless of the argument. One home for the epoch
  semantics; the apply call sites always pass the real object, so the
  builder's fallback only guards hypothetical future callers.
- **Apply-json `checkpoint` key semantics.** Null when validation.sh
  did not run (bailout/clarification/dry-run/drift-refused), the
  known-zero object when it ran unconfigured, the detail object when a
  checkpoint executed — mirroring the telemetry stamp rather than
  inventing a third vocabulary. Key list stays owned by
  `format_apply_json`'s docstring (one-home rule).
- **Both halves of the materialization rule.** The runner restores the
  mode from the tree entry (`git ls-tree`, falling back to 0o755) AND
  invokes via `bash` — either alone satisfies disposition 5; doing
  both makes silent non-execution impossible. The D8 test asserts on
  executed output, so a regression in either half still fails loudly.
- **The worker band is written by the checkpoint runner.** The
  `=== worker validation.sh ===` band is the runner's last act, so all
  banding lives in one function and `run_validation_sh` is untouched —
  which is also what keeps unconfigured projects' logs byte-identical
  to today's (asserted in the suite).
- **`bin/bale` is untouched.** Session A adds no flags, and the apply
  path's imports live in `bale_apply.py` (which gained
  `run_blind_checkpoint` in its lazy import block). The D7 "wiring"
  line turned out to be already satisfied by the module layout.
- **`claude/context/bale-internals.md` is untouched.** Its §2.5
  schema snippet was not extended by the [staging] (v0.3.7) or
  [identity] (v0.3.8) landings; I followed that precedent rather than
  diverging inside a code session. If the precedent is an accident
  rather than a policy, a small doc session can true it up — flagged
  in `deferred`.

## Look closely on review

- `bin/bale_apply.py`, the state-derivation block: the PASS/HOLD
  envelope logic and the three attributed log messages. The existing
  no-checkpoint paths are byte-identical by construction (the new
  branches only fire when `checkpoint_result` is not None) — worth a
  glance to confirm you read it the same way.
- `schemas/telemetry-record.schema.json`: I first regenerated the file
  through `json.dump` and it exploded the hand-formatted inline arrays
  into a spurious whole-file diff; I reverted and re-inserted the
  `checkpoint` block as a targeted text edit matching the existing
  style. The diff is now insertion-only — verify it renders that way
  on your side too.

## Environment gaps and the one predicted claim

- `scripts/build.sh` and `install.sh` are not in this request's tree,
  so `tests/test_release_packaging.py` (7 tests) errors in my sandbox
  — at baseline, before any edit of mine. My `validation.sh` therefore
  runs the packaging suite as its own check (it will execute in your
  staging, where both files exist) and the suite claim for it is a
  **prediction, not an observation**: the release lists cover the
  install trees (`bin/`, `docs/`, `schemas/`, `tools/`), this session
  adds no new file under any of them, and the new `tests/` file is
  outside the lists' domain — so I claim `pass`. If it fails, the
  likeliest cause is a coverage rule I couldn't see; the check is
  split out precisely so that failure is attributed to the right
  place.
- The brief's D1 cites `context/bale.toml`'s header; that file is not
  in this request's tree. Harmless — the quoted text rides in the
  brief itself and nothing here depended on the file.

## Proposals

- **Ship `scripts/build.sh` + `install.sh` in the execution-context
  set** for sessions whose validation runs the full suite. Grounded in
  this session: the ratified execution-context manifest set (bin/,
  schemas/, the four globals, tools/response_lint.py) leaves the
  packaging suite unrunnable in the worker's sandbox, which forced a
  predicted rather than observed claim and a split-out check. One
  extra include per pack closes the gap.
- **Dry-run prediction for the dangling-checkpoint refusal.** Session
  B's step-15 gate is spec'd to predict under `--dry-run`; when it
  lands, extending the same prediction to the dangling refusal is a
  small additive follow-up (resolve the target base read-only before
  the dry-run exit). Only worth doing if you use dry-run as a
  pre-apply gate on checkpoint-configured projects.
