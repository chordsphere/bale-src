# notes — 2026-08-07-board-35-pack-guards-013

One new file, `tests/test_pack_guards.py`, in the tests-directory
forecast. No out-of-forecast paths; `tests/harness.py` was in-forecast
but I didn't touch it — see the promotion note below.

## Census

Per the arc's precedent: what's covered, what's excluded, and why per
exclusion. Surface enumerated from the shipped `bin/bale_pack.py`
(constants §1, filter chain §2, `walk_for_pack` + `PackCaps` §3,
`_prompt_soft_breach_action`, and cmd_pack's breach-handling loop) and
`bin/bale`'s argparse wiring before anything was written.

### Covered (20 tests)

- **`--max-files`**: refusal one past the cap (message names count and
  cap, projection block shown, refusal is pre-sid: no session, no
  outbox tarball); pass at exactly the cap (the `>= hard + 1` trip is
  inclusive of N).
- **`--max-size`**: refusal one byte past a `2K` cap (exercising the
  1024-based K-suffix parse on the way); pass at exactly the cap
  (`total_bytes > cap` is strict).
- **`--max-depth`**: refusal at depth cap+1 with the offending path
  named in the message; pass at exactly the cap (the docstring's "a
  cap of N means files up to N directories deep are allowed").
- **Cap flag validation**: `--max-files 0`, `--max-size 12Q`,
  `--max-depth -1` each refuse at input validation with their message,
  pre-walk.
- **`--force` past a hard cap**: the identical oversized pack
  proceeds; the FORCE audit line names the bypassed breach; all three
  files land in `context_included`.
- **`--force` past the piped soft-breach refusal**: the refusal text
  names `--force` as the escape hatch; pinned that the hatch works and
  is logged as a FORCE event naming the soft cap.
- **`--exclude`**: pattern prunes a path the `--include` would pull
  in — asserted from the packed tarball's member list *and* the
  shipped manifest's `context_included`, per the brief, not the pack
  report.
- **`.baleignore`**: same assertion basis; also pins that
  `.baleignore` itself always ships in `context/` (cmd_pack's
  force-include branch), so the worker can see what filtered its view.
- **Composition**: `.baleignore` + `--exclude` is a union
  (`build_pack_matcher` feeds file lines and session patterns through
  one matcher); a path matched by either is dropped.
- **`--exclude` negation**: leading `!` refuses via the matcher's
  negation guard, message naming the offending pattern.
- **Exclude-everything**: the empty surviving set refuses with the
  widen-your-include message rather than packing nothing.
- **Piped soft breach**: no TTY → refusal outright (the v0.2.4
  posture), message naming the unavailable prompt; pre-sid.
- **`[n]`**: aborts pre-sid, with the projection block and breach line
  shown first.
- **Unrecognized input + bare Enter**: re-prompt on `x`, then the
  bare-Enter default is abort.
- **`[e]` with patterns**: session-only patterns collected, matcher
  rebuilt, re-walk clears the breach, pack proceeds without the
  oversized file.
- **`[e]` with an empty collection**: "no patterns added" → re-prompt
  instead of an identical re-walk; `[n]` then aborts.
- **`[y]`**: proceeds at the breached scope; the oversized file ships
  in `context_included`.

### Excluded, and why

- **The soft *file-count* breach (10,000 files).** The soft caps are
  deliberately not user-tunable (PackCaps docstring), so crossing this
  one means generating 10,001 real files per test — the classic budget
  eater the brief warns about. The soft-*size* cap crosses with a
  sparse file at zero generation cost and drives the identical prompt
  code path (`soft_breaches` is one list; the prompt doesn't branch on
  which cap filled it), so the count variant buys no new behavior for
  its runtime.
- **`--force` with nothing tripped** (the "no thresholds tripped"
  audit line). Logging-only branch with no guard behavior; left to
  keep the suite lean.
- **`--force` bypassing the home-directory refusal.** Same flag,
  different guard (`refuse_system_dir`), and the sandbox repo can't
  sit under a refused directory without simulating one — that's the
  system-dir refusal's own test surface, not the cap family's.
- **`--verbose` per-path drop lines.** Adjacent (it names which filter
  dropped each path) but a distinct v0.3.35 surface with its own
  streaming contract; the filters themselves are asserted from the
  packed artifact here.
- **`gather_files_for_pack`.** Internal convenience entry point; the
  suite drives the shipped CLI end to end per the arc's doctrine, and
  cmd_pack uses `walk_for_pack` directly.
- **Negation patterns *inside* `.baleignore`** (as opposed to
  `--exclude`, which is covered). The refusal fires, but on the
  fully-specified CLI path it surfaces with the session-exclude
  wording ("invalid session exclude pattern") even when the offending
  line came from the file — see Proposals. Pinning tests-only
  shouldn't freeze a message I'd propose changing.
- **`largest_dirs` content beyond presence.** The projection block's
  presence (header line) is asserted at the refusal and the prompt;
  its per-directory arithmetic is formatting, not a guard.
- **`100MB`-style two-char suffix parsing** (`KB`/`MB`/`GB`
  tail-strip). The one-char suffix and the malformed-value refusal pin
  `parse_size_arg`'s contract ends; the two-char variant is interior
  parsing detail.

## Runtime (§7.6)

The brief's numbers: 300 tests at ~101s against the two-minute
target. In my build environment the pre-change suite ran 303 tests in
~68s and the post-change suite 323 in ~75s — a ~7s addition here,
which scales to roughly +10s on the architect's clock, i.e. ~111s
against the 120s target. Material, but under target, so I did **not**
gate anything behind `--slow`: the two generation-heavy-ish cases (the
`[y]` proceed and force-past-soft, ~1.5s each — the only tests that
actually copy the 100MB sparse file) are both behaviors the audit
names, there is no existing `--slow` convention in the test tree to
ride, and inventing one to save ~3s didn't clear the bar. If the
architect's measured wall lands closer to 120s than my scaling
predicts, those two tests are the right ones to gate — flagged in
their docstrings. See also Proposals.

## Judgment calls

- **Sparse file for the soft breach.** The walk projects `st_size`
  (`stat`), so a one-byte write at offset 100MB crosses the soft size
  cap with no real disk or generation cost; only the two
  proceed-past-breach tests pay the copy. `SOFT_SIZE_CAP` is mirrored
  in the test file rather than imported — the harness doctrine drives
  bale as a subprocess by absolute path, never imports its modules —
  and a drifted constant fails loudly on the missing breach marker.
- **Harness promotion: not taken.** The tree-size helpers
  (`write_payload`, `write_soft_breach_payload`) and the tarball
  reader (`shipped_context`) have exactly one consumer, this file, so
  per the one-harness trigger they stay test-local. No second consumer
  landed this session.
- **Per-class sandboxes stay per-test** (ADR-0005): 20 sandboxes is
  most of the suite's non-copy runtime, but sharing state across
  tests would break hermeticity — a successful pack leaves an open
  session whose forecast gates every later pack in the same repo,
  which is exactly the cross-test interference the doctrine exists to
  prevent.

## Proposals

### Name the pattern's source in the negation refusal

**What:** When `build_pack_matcher`'s combined parse trips the
negation guard, the failure message says "invalid session exclude
pattern" regardless of whether the offending line came from
`--exclude` or from `.baleignore`. On the wizard path the file was
pre-validated by `load_baleignore`, so the wording holds there; on the
fully-specified CLI path a negation line in `.baleignore` reaches this
branch and gets attributed to the session. Split the message by
source, or re-validate the file lines separately before composing.

**Why:** Observed while enumerating the composition surface this
session (the code comment at the `fail()` assumes the file "was
already validated by load_baleignore in any surface that called it",
which the fully-specified path doesn't). A user who typed no
`--exclude` and is told their session exclude pattern is invalid will
look in the wrong place. I deliberately did not pin this wording in
the suite so the fix isn't fighting a test.

**Scope hints:** `bin/bale_pack.py` (`build_pack_matcher`), plus one
test here once the wording settles. Independent of other queued work.

### A `--slow` convention for the test tree, if the wall keeps creeping

**What:** An opt-in env-var gate (e.g. `BALE_TEST_SLOW=1` +
`skipUnless`) for generation-heavy cases, established once as a
harness-level helper rather than per-suite.

**Why:** This session brought the scaled wall to ~111s of the 120s
target with nothing left to trim that doesn't cost audit-named
coverage. The *next* generation-heavy suite won't have that luxury;
better to introduce the convention deliberately (with `validate.sh`
and the docs knowing about it) than as a side effect of whichever
session first overruns.

**Scope hints:** `tests/harness.py`, `validate.sh`, a line in the
testing docs. Only worth doing when a session actually needs the gate.
