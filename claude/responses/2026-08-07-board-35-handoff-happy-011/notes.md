# notes.md — 2026-08-07-board-35-handoff-happy-011

## Out-of-forecast paths (per-path admission at apply)

- **`tests/test_handoff_happy.py`** (created). The forecast named
  `tests/test_install_precheck.py`; I took the brief's "defensible"
  branch and gave the happy-path suite its own home. The precheck file
  is about the broken-install refusal gate; this suite is about the
  repackaging pipeline itself — different reader, different fixture
  shape (it applies a real bailout; the precheck suite never gets past
  the gate). `test_install_precheck.py` is consequently unmodified —
  the forecast entry stands unused, which the forecast model permits.

## What the happy path actually does — surprises

- **`context_included` is `context/`-prefixed.** The brief's sketch
  ("handoff.md plus reading-plan files") is right, but
  `build_request_manifest` stamps every entry as `context/<rel>` —
  my first draft of the suite pinned the bare names and failed. The
  tests now pin the shipped form (`context/handoff.md`,
  `context/hello.txt`).
- **The forecast and the read set coincide by construction on the
  handoff path.** One value (`handoff_scope`) feeds the blindness
  gate, the manifest's `resolved_scope` stamp, and the registry
  record — the suite asserts the stamp and `scope.json` agree, so a
  future desync of that one-source rule breaks a test.
- **Verbose lands in the session log for free.** Handoff's build call
  runs after `set_log_file`, so the trail double-writes (terminal +
  `.bale/logs/<new-sid>.log`) with no extra plumbing — pinned in the
  verbose test, since it's behavior the flag's help text promises.
- Nothing else diverged from the brief's summary: goal verbatim,
  constraints/out_of_scope reset, `expects_probe` at claude-decides,
  `depends_on.previous_response` at the bailout.

## Coverage census

Now covered: the repackaging E2E (bailout → apply → handoff → new
request tarball with the full injected surface), sid derivation (same
slug, fresh counter), lineage pointer, goal inheritance, reading-plan
pre-pack + forecast recording (one-source assertion), the plan-less
whole-tree fallback (pinned AS-IS per the standing watch — not
remedied), and `--verbose` both directions.

Still not covered: `--edit-goal` (needs a pty + a scripted editor;
none of the suites drive $EDITOR editing today), the repeat-bailout
lineage warning's happy-warn path (test_telemetry_promotion covers
adjacent telemetry, not the warning text), the
missing-request-manifest fail path ("cannot inherit goal"), and
`--force`/home-dir semantics on handoff specifically. All are refusal
or edge surfaces, not the gap-7 happy path.

## One-apply-behind

Handoff is not the apply path, and the flag is default-off: the
session's own landing gives no old-behavior dose. The first
`bale handoff --verbose` run after this lands already uses the new
`bin/bale`. Stated per the brief; nothing to sequence.

## Proposals

### Thread --verbose into handoff's gather_files_for_pack call

**What:** `cmd_handoff` calls `gather_files_for_pack(repo,
extracted_paths)` without the `verbose` kwarg the function already
carries, so `handoff --verbose` streams the build trail but not the
filter-chain drop narration pack streams.
**Why:** The accepted fold-in's text scoped this session to the
`build_request_tarball` call, so I stayed in that lane — but the
asymmetry is visible to a user: a reading-plan file silently dropped
by the filter chain (typo, gitignored) is exactly what `--verbose`
exists to narrate, and the dropped-candidates line in the session log
is a coarser signal.
**Scope hints:** `bin/bale` cmd_handoff (one kwarg), plus one
assertion in `tests/test_handoff_happy.py`. Trivial rider for the
next session touching that surface.

### Update build_request_tarball's docstring stale sentence

**What:** `bin/bale_pack.py`'s `build_request_tarball` docstring ends
"`bale handoff` (the other caller) passes nothing and stays
byte-identical — the flag is pack-scoped for now." This session makes
that false.
**Why:** `bale_pack.py` was a hard constraint this session (sibling
sessions open), so the sentence ships stale. One-line prose fix, no
behavior.
**Scope hints:** `bin/bale_pack.py`, docstring only; rides any next
session with that file in forecast.
