# notes.md — 2026-08-11-board-10-sandbox-wrapper-001 (response-002, retry)

## Why response-001 HOLDed, in one paragraph

Both HOLD lanes were one root cause. Response-001's ro sweep read each
findmnt line's VFS options and restated them on the remount call,
intending flag preservation. On the target machine `/run/user` is an
**overmount pair** — a shadowed `nosuid,nodev,noexec,noatime` tmpfs
under a topmost `rw,relatime` tmpfs (operator findmnt, pasted in
session chat). The sweep's shadowed-line call carried `noatime`, but
the kernel resolves the path to the *topmost* mount, whose locked
atime state is `relatime`; in a user namespace a locked-flag mismatch
is EPERM ("permission denied" + the dmesg hint — exact message shape
reproduced in the build environment). The self-probe refused, so the
checkpoint's S1 guard (exercising `run_confined` as a library from
the staged module) and every suite that spins an apply failed on the
same refusal. Nothing ran unconfined; the reconciliation table showed
DISAGREE on exactly the five environment-invalidated claims. The
system behaved as designed around a real bug.

## The diagnosis chain (all verifiable)

1. Build-env experiment: locked-flag EPERM produces the exact
   "permission denied." + dmesg-hint message shape.
2. Build-env strace: util-linux **auto-merges** the topmost mount's
   current flags on `remount,bind` (passed MS_NOSUID|MS_NOATIME
   unbidden) — so response-001's keep-filter never added safety.
3. Operator probes: the /run/user overmount pair (findmnt) and a
   clean `mount(..., MS_RDONLY|MS_REMOUNT|MS_BIND|MS_RELATIME) = 0`
   from a plain remount (strace) — proving plain remount succeeds on
   the exact failing target.
4. Build-env repro: the overmount pair erected under locked flags —
   old call EPERMs with the identical message, new call passes; now a
   permanent behavioral regression test
   (`test_overmounted_path_with_mismatched_locked_flags`).

The README's trial attested literally `remount,bind,ro` — which was
always correct. The failure was introduced by response-001's
flag-restating "improvement", and the build environment has no
overmounts to catch it. Not environment drift: the trial and the
HOLD are both consistent with /run/user being an overmount all along.

## What changed vs response-001 (three files)

- **bin/bale_sandbox.py** — the sweep: iterate findmnt TARGETs,
  deduplicate stacked targets, issue plain `remount,bind,ro` per
  target (flag preservation is libmount's merge), skip-and-log a
  target that no path resolves to, and on any reachable target's
  failure die loudly with the mount's full findmnt record
  (TARGET,FSTYPE,VFS-OPTIONS,FS-OPTIONS,PROPAGATION) in the sentinel
  so the next environment surprise self-diagnoses without a probe
  round-trip. `_PRESERVED_VFS_FLAGS` removed; module docstring step 2
  rewritten with the mechanism truth and the HOLD's lesson.
- **tests/test_sandbox_wrapper.py** — sweep-shape units updated (plain
  remount asserted, flag-restating asserted ABSENT, dedupe and
  unreachable-skip asserted present, sentinel enrichment asserted);
  the overmount regression added (15 tests now).
- **BALE.md** — the §8.5 sweep sentence states dedupe, the
  unreachable-skip rule, and the enriched loud failure.

Everything else ships byte-identical in intent to response-001
(re-mirrored and re-hashed by craft_response, never carried).

## Decisions to ratify (§5.4) — additions to response-001's list

1. **The unreachable-target skip rule.** The pinned design said
   "strict sweep, NO allowlist of skippable mounts." This retry keeps
   the no-name-allowlist principle but adds two capability-based
   exceptions: stacked duplicates at one path are one reachable mount
   (dedupe), and a listed target that does not resolve (shadowed by a
   higher overmount) is skipped and recorded in the session log —
   what no path reaches, the confined child cannot write to either.
   This is judgment extending the pin; if you want shadowed-submount
   encounters to be loud failures instead, the skip branch is
   four lines to invert.
2. **Flag preservation delegated to libmount's merge** rather than
   restated. The strace evidence on both machines is the basis; the
   unit tests pin the plain-remount contract so a future "helpful"
   restoration of flag-restating fails tests.
3. Response-001's ratification list stands (escape-flag spelling,
   /usr probe target, capability-gated test tiers, rider test home,
   packaging-list registration).

## Suite runtime — the crossing resolved itself

Response-001 measured 127s here (baseline 103s) and flagged the 120s
target crossing. The rewritten sweep dropped per-spin cost 98ms→72ms
(the per-mount bash option-parsing loop was the dominant term, and
dedupe removes redundant remounts), and the full suite now measures
**88–89s across two consecutive runs (339 tests)** — under both the
target and this container's pre-sandbox baseline. Treat the absolute
numbers as this-container-relative (cache warmth between runs is a
plausible confounder in the baseline figure); the margin risk I
escalated in response-001 is withdrawn, and the --slow deferral is
dropped from the manifest. Your WSL2 numbers remain the ones that
count.

## Operator mechanics for this retry

- `bale retry` re-runs the same pipeline, and the out-of-forecast
  admission is per-invocation, never carried (the flag help text says
  so): the retry needs `--allow-out-of-scope install.sh
  --allow-out-of-scope scripts/build.sh` restated.
- One-apply-behind still holds: this retry executes under installed
  bale 0.4.3 (unconfined pipeline); the suites in staging exercise
  the fixed confinement directly, including on your /run/user
  topology. The first bale-driven sandboxed apply is next session's.
- The held response-001 branch is superseded by this retry's commit;
  nothing to revert manually.

## Compaction disclosure (CLAUDE.md §11.6)

The session compacted once, mid-build of response-001 (disclosed in
that response and re-disclosed here since notes travel per-response).
All artifacts were re-grounded from disk; every hash in this
manifest was recomputed by craft_response after the fact; every
suite ran after the retry edits. feedback.self_reported records
compaction_occurred with this section as the disclosure_ref.

## Probe facts

This retry is built on an operator probe round (session chat, three
commands): the /run/user findmnt record, the strace'd successful
plain remount inside the namespace, and dmesg (no kernel note).
Those outputs are quoted in the diagnosis chain above and are the
ground truth the fix targets.
