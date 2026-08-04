# notes.md — 2026-08-04-board-6-superset-gate-005

## Decisions to ratify

- **VERSION stays 0.3.27.** Session A landed the checkpoint core
  without bumping the constant (the shipped tree still reads 0.3.27,
  and A's surfaces are tagged "board 6 session A" rather than a
  version). I followed that precedent: B's surfaces are tagged
  "board 6 session B" and the constant is untouched. If the arc is
  meant to bump per session, say the word and a one-line follow-up
  (or session C) trues it up.
- **Step-15 siting and physical order.** The gate sits immediately
  after step 14's block in the pipeline, which is *before* step 13's
  generated-artifact denial physically (step 13 already sat after
  step 14 in code; the numbered anchors are logical, not positional).
  The documented ordering consequence — a read-only session's changes
  hit step 14 first and never reach step 15 — is pinned by the suite.
- **Set semantics at the gate.** Required names are deduplicated
  preserving config order; matching is exact-string per the §5.3
  canonical-identifier rule; the refusal renders the required set,
  the declared list, and the missing names so a paraphrased check is
  visible as a near-miss. The accessor tolerates duplicate config
  entries (the gate dedupes) but is strict on shape — non-list,
  non-string, or empty entries are fatal, mirroring
  `staging.untracked_inputs`.
- **Wire names.** The apply-json detail key is `required_checks`
  (fields: missing / required / declared / overridden), owned by
  `format_apply_json`'s docstring per the one-home rule. The
  telemetry field is `attempts[].required_check_overrides`,
  always-a-list exactly like `overridden_paths` — including on a
  `required-check-refused` attempt, where it carries what a partial
  override admitted while other names refused.
- **The rider's blast radius.** The dry-run dangling-checkpoint
  prediction is gated on a configured checkpoint, so unconfigured
  projects' dry-run behavior is byte-identical to before. One
  deliberate consequence: a *checkpoint-configured* project's dry-run
  now resolves the session's target branch (read-only), so a session
  with a missing origin stamp or a deleted target branch gets that
  refusal at dry-run time too — which is an honest prediction (a real
  apply refuses the same way at step 5's resolution), but it is new
  dry-run behavior for those degenerate states.
- **merged_config is now read twice per apply** (once at the step-15
  gate — shared with the dry-run rider — and once at stage time,
  which deliberately re-resolves per the existing comment). Both
  reads are two small files; I did not thread one through to the
  other because stage-time re-resolution is documented as what makes
  retry inherit the strategy structurally.
- **`[validation] required` walks with `_prompt_path_list`.** The
  wizard's list interface splits on colons; check names with colons
  in them can't be entered through the wizard (hand-editing bale.toml
  still works, and the strict accessor is what apply reads). Existing
  check-name conventions ("vue-tsc --noEmit", "tests") don't use
  colons, so I took the canonical list walk over inventing a second
  list interface.

## Look closely on review

- `bin/bale_apply.py`, the step-15 block: the refusal mirrors the
  drift gate's structure (no SystemExit, so the cmd wrapper never
  double-records "rejected"); worth confirming you read the
  telemetry-vs-dry-run branching the same way.
- `schemas/telemetry-record.schema.json`: targeted text edits per
  session A's precedent (no json.dump regeneration), so the diff
  should render as enum-value insertions, two description extensions,
  and one new property block. Verify it renders that way on your
  side too.
- The §11 header's phase note still says "steps 1–13 of section 8.1"
  — that was stale before this session (step 14 landed in v0.3.10)
  and I left it untouched rather than widen the doc lane; proposed
  below.

## Environment gaps

- `context/tools/craft_response.py` was not in the shipped tree (only
  `tools/response_lint.py` under `context/tools/`), so every suite
  errored at baseline in my sandbox: the harness's scratch installs
  fail bale's injected-files check. I satisfied it with the
  request-root injected copy of the same file (bale injects it from
  the install, which is built from the repo, so the bytes should be
  identical); with that in place the baseline ran 177 tests green and
  the final tree runs 192. Unlike session A, no claim this session is
  a prediction — both suite checks were observed in-sandbox, and the
  shipped `scripts/build.sh` + `install.sh` (session A's adopted
  proposal) made the packaging suite runnable here. `bale.toml` is
  also absent from the tree, as in session A — harmless again.

## Proposals

- **Ship `tools/craft_response.py` in the execution-context set.**
  Grounded in this session: the ratified set covers
  `tools/response_lint.py` by name but the harness requires every
  `INJECTED_TOOLS` member in the install copy, and the crafter joined
  that tuple in v0.3.19. Same species as session A's
  build.sh/install.sh proposal (adopted this pack); one more include
  closes the last baseline-red gap. Scope hint: the pack command's
  include list, no code change.
- **True up §11's header phase note.** "Failure → reject before
  staging (steps 1–13 of section 8.1)" predates steps 14 and 15,
  both of which also reject before staging. A one-line doc fix,
  suited to the master-deltas vehicle or any doc session touching
  BALE.md §11. Only the header sentence; the rows themselves are
  accurate.
