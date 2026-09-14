# notes.md — 2026-09-14-board-78-admission-prompts-001

One-apply-behind, as prior workers have flagged: the apply that lands
this tarball runs the old apply code one final time — no prompts, the
placeholder remedy, the old hook default. Everything below is live
from the next apply.

Every `changes[]` path is inside the write forecast. No out-of-forecast
work.

## The probe-site fact (the desk asked for it here)

The sandbox self-probe fired *after* staging had been populated: it
sat in `bale_staging.stage_response`, right before `apply.sh` — so the
old refusal wiped a staging tree it had already built and recorded
`rejected` from inside the staging step. Per your Q1 answer it now runs
once in `apply_pipeline` at the seam after the dry-run return and
before the §8.2 session stamp — after every manifest-only gate (drift,
base drift, required check, generated-artifact and bundle denials,
file hashes), before anything is consumed. The later per-script
`ensure_verified` calls are the cached no-op. A namespace-less host
now learns about it a few gates later than a drift refusal and a few
steps earlier than before; `bale open`'s dry-run leg still reaches the
probe through its own first call (untouched).

Ordering is pinned end to end
(`test_drift_refuses_before_the_sandbox_prompt`): a namespace-less
operator with drift is never asked the sandbox y/N only to be refused
on drift afterwards.

## Calls I made (flagged; ratify or correct)

- **Quoting.** The desk rule says the filename is *quoted*, so every
  token on the composed line is single-quoted unconditionally
  (`shlex.quote` leaves a safe token bare, which would have made the
  line's shape vary by filename). An embedded `'` takes shlex's own
  `'"'"'` splice; `shlex.split` round-trips it (pinned).
- **Paths on the composed line are the gate's normalized form**
  (`scope_path`), not the exact spelling typed. A typed `./lib/b.txt`
  comes back as `lib/b.txt` — the same path, the flag still admits it.
  If "verbatim" meant character-for-character, say so and I'll thread
  the raw argv through.
- **Prompt-admitted drift rides the sandbox remedy.** If the operator
  admits drift at its y/N and then declines the sandbox y/N, the
  composed `--no-sandbox` line carries `--allow-out-of-scope` for the
  paths just admitted — nobody typed them, but the paste is meant to be
  one re-run, not a re-prompt. Pinned by
  `test_prompt_admitted_drift_rides_the_sandbox_remedy`.
- **A partial `y` admits nothing.** With three drifted paths, `y`, `y`,
  Enter refuses with `overridden_paths: []` — the constraint says
  nothing lands partially, and I read that as "the prompt's admissions
  are all-or-nothing" rather than "stamp the two yeses on a refused
  attempt". The refusal block gets an `admission prompt: declined` row
  so a log reader can tell a declined prompt from an un-prompted one.
- **Typed paths are not re-asked.** A path already admitted by a typed
  `--allow-out-of-scope` stays `flag`-sourced and is skipped at the
  prompt; only still-refused paths are asked. A mixed run stamps both
  vocabularies (pinned).
- **The sandbox decline rides `fail()`** as you ruled: outcome
  `rejected`, `sandbox_confined: true`, `sandbox_off_source: null` —
  `record_rejected_attempt` already stamps exactly that. The
  `fail()` message repeats the composed line and the config key so the
  stderr face (what the existing namespace-less test pins) is
  actionable on its own; the human block goes to stdout.
- **`sandbox_escaped` stays false under a prompt admission.** Its
  flag-only meaning is unchanged; `sandbox_off_source: "prompt"` is
  the fact. The network-grant "not exercised" note now names whichever
  of the three escapes actually bypassed.
- **Store shape.** `<install>/user/hook-acceptances.json`, a JSON
  object keyed by sha256 hex; each value carries `script` (the resolved
  absolute path as configured), `hook`, `layer`, `accepted_at` (UTC
  ISO). Written atomically (temp + `os.replace`). Absent → empty,
  silently. Malformed or not-an-object → empty *with a logged warning*
  naming the file — every project hook asks again until it is fixed,
  never a silent accept. Only a first interactive accept of a
  project/`configured` hook writes it; a `[Y/n]` Enter on an already-
  remembered script does not rewrite the entry (no timestamp churn).
- **The prompt line shows its basis.** `default: accept — these exact
  bytes were accepted before (sha256 …, remembered in …)` or `default:
  decline — project-layer hook not yet accepted at this install`, so
  the operator sees why Enter does what it does. A hash read failure
  logs and falls to the decline default.
- **`configured` (neither-layer) hooks** are treated exactly like
  project-layer ones, per the constraint's "unlabelled" wording.
- **No new telemetry outcome, no new §11 row.** The sandbox refusal
  is documented in the existing §8.5 paragraph as sentences; the code
  comment cites that paragraph rather than inventing a step number.

## Test structure worth a look

- **Host independence.** The sandbox E2E class puts a shim `unshare`
  (exits 1) first on PATH, so the refusal and its y/N run identically
  on a host with namespaces and on the work server. The drift and hook
  classes commit `[sandbox] enabled = false` in their fixture repos —
  they test prompt logic, not confinement, and without that a
  namespace-less host would hit the new sandbox prompt and derail the
  answer sequences. I ran the whole shipped set both ways: with
  namespaces (215 tests, 1 failure — see Claims) and with `unshare`
  removed from PATH (the new suites pass; the shipped
  `test_apply_operations.py` fails there exactly as it did before this
  session, since it is not namespace-gated — pre-existing, not mine).
- **`_minimal_record` / `_load_module`** are duplicated in the new unit
  suite rather than imported from `test_telemetry_extensions.py`;
  importing a test module for its helpers would couple two suites'
  load order. The harness is the right home if a third consumer
  appears (Proposals).
- `test_hook_acceptance.py` is the first suite to mention
  `post_apply_pass` and `hook_auto_accept`, as the brief predicted.

## Claims

- `session assertions` — **observed**, the rehearsal above passed.
- `unittest: touched and new suites` — **predicted**, not observed,
  though narrowly: every test in the group ran green here except
  `test_stats_fixture_corpus_validates_clean`, which needs
  `tests/fixtures/stats_corpus/` (in `base_files`, not in the request
  — `includes_missing`). It passed before my change in the same way it
  fails here (fixture absence), so I expect green in your tree.
- `unittest: full discovery (--slow)` — **predicted**: 215 tests ran
  here, the repo has more. The suites the brief names as pinning the
  drift gate but not shipped (`test_forecast_ledger.py`,
  `test_required_check_gate.py`, `test_stats_drilldown.py`) are the
  ones I cannot see; if any of them asserts the old
  `` `bale apply <tarball> --allow-out-of-scope <path>` `` template
  text of the refusal, it will fail and the fix is the assertion.
- `validate.sh (install sanity)` — **predicted**: 88/89 here, the one
  failure is "README.md present" (README not shipped).

`validation.sh` rehearsed in a staging-shaped copy (originals overlaid
with `files/`, `apply.sh` run, manifest placed); every check other than
the two fixture-absence failures above passed, and the `--slow` tier
ran in 27s.

## Surprises

- Nothing in the shipped tests pinned the placeholder remedy text, so
  no existing assertion needed rewriting for the composed line; only
  the two `sandbox_off_source` enum pins widened.
- `format_summary_block` already promises trailer lines are never
  wrapped ("copy-pasteable command hints that must not break across
  lines") — the one-physical-line rule had a home waiting for it.

- `response-manifest.schema.json` says the feedback `provenance` block
  is the request's provenance "echoed verbatim" but sets
  `additionalProperties: false` without `base_files`, so the lint
  rejects a verbatim echo of this request. I dropped `base_files` from
  the echo (everything else is verbatim). Schema-side fix is one line;
  out of scope here, noted for the desk.

## Proposals

- **What:** composed remedy lines for the `--accept-base-drift` and
  `--allow-missing-required-check` refusals (the brief invited this as
  a proposal). **Why:** `compose_admission_command` already renders
  both flags; the two renderers (`format_base_drift_refusal`,
  `format_required_check_refusal`) still close with templates, and
  they are the next copy-to-desk round trip. **Scope hints:**
  `bin/bale_report.py` (two renderers), the two gate call sites in
  `bin/bale_apply.py`; prompts stay out by desk ruling.
- **What:** move `_minimal_record` / `_load_module` from
  `test_telemetry_extensions.py` into `tests/harness.py`. **Why:** the
  new unit suite is the second copy. **Scope hints:** `tests/harness.py`,
  the two suites; trivial.
- **What:** a `bale config` view of the hook acceptance store (list,
  forget-one). **Why:** today "forget" is hand-editing JSON; the store
  is auditable but not operable. **Scope hints:** `bin/bale_config.py`
  (`cmd_config_*`), `bin/bale` parser; after this lands.
- **What:** gate `test_apply_operations.py` on namespaces or give it
  the config-off fixture. **Why:** it fails on the namespace-less host
  today for a reason unrelated to what it tests. **Scope hints:**
  `tests/test_apply_operations.py`; one line either way.
