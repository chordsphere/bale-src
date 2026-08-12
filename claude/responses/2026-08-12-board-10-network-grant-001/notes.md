# notes — 2026-08-12-board-10-network-grant-001

## Probe record (TARBALL.md §4.5)

One paste-back probe round, pre-build, slug
`board-10-network-grant`. Trigger: `scripts/build.sh` documented a
version coupling into `validate.sh`, which was not in the request;
shipping the VERSION extraction blind risked breaking every future
install's validate run. Findings, all load-bearing:

- `validate.sh` is 314 lines; full text returned and reconstructed
  byte-exact (sha256
  `a0da23e90a9249a236678f1c9a83736205bd8309aff723422075593d282d2a32`,
  matching the probe's own hash) before editing. Its CLI-surface
  section scrapes `bin/bale`'s `VERSION = "…"` line (line 204) and
  fails loudly when absent — confirmed necessity for the third
  out-of-forecast file below.
- `scripts/reinstall.sh` and `upgrade.sh` have **no** version
  coupling (grep exit 1 / no matches). `upgrade.sh`'s
  `REQUIRED_RELEASE_MEMBERS` is a subset check, so it needs no
  `bin/VERSION` entry.
- Complete reader set of the old constant: `bin/bale`, `validate.sh`,
  `scripts/build.sh`, `tests/test_release_packaging.py` — all four
  updated in this response; nothing else on the machine reads it.
- Operator environment: WSL2, kernel 6.6.

## Out-of-forecast admissions (drift gate will name these)

1. **`install.sh`** — expected admission per the brief:
   `INSTALL_LAYOUT` gains `bin/VERSION` (one line) so the
   install/release list-agreement gate holds.
2. **`scripts/build.sh`** — expected admission per the brief:
   `RELEASE_FILES` gains `bin/VERSION`; version resolution and the
   version-tag drift guard read `bin/VERSION` (die messages updated;
   `test_release_packaging` follows).
3. **`validate.sh`** — the probe-confirmed one: repointed
   `EXPECTED_VERSION` to `bin/VERSION` (head -n 1 + whitespace trim,
   loud fail when missing/empty), added a `bin/VERSION present`
   layout row, updated the symlink SKIP message. Without this, the
   next install's validate.sh fails its version rows against a
   `bin/bale` that no longer carries the constant.

Apply hint: `--allow-out-of-scope` once per path (README has the
full command).

## First-sandboxed-apply findings (the brief asked for surprises)

This response's scripts are the first production traffic through the
ADR-0016 sandbox. Two real discoveries, both verified empirically in
a container with working user namespaces:

### 1. Inherited `/sys/class/net` is not netns-accurate — `/proc/net/dev` is

Inside `unshare --net`, the **inherited sysfs mount keeps showing the
mounting namespace's devices**: `ls /sys/class/net` listed the host's
`eth0`/`ifb0`/`ifb1`/`lo` from within a fresh network namespace,
while `/proc/net/dev` correctly showed only `lo` (the prologue mounts
a fresh proc, so procfs tracks the sandbox's own netns; nothing
remounts sysfs). Consequences:

- A probe asserting the **loopback-only floor** via a bare
  `/sys/class/net` listing will misread the floor as breached — it
  sees the host's interfaces even with `--net` in force.
- The brief's parenthetical named `/sys/class/net` as the checkpoint's
  probe surface. I could not read the checkpoint (correctly out of
  bounds), so: **if `claude/checkpoints/current.sh` asserts the floor
  via `/sys/class/net` without remounting sysfs, it will fail against
  correct sandbox behavior.** `/proc/net/dev` (or `ip link`, or a
  fresh `mount -t sysfs` inside the child) is the accurate surface.
- Everything I shipped probes `/proc/net/dev`: the behavioral tests,
  the E2E validation fixtures, and the suite's module docstring now
  records the sysfs caveat.

### 2. The suite was not confinement-self-hosting (fixed)

S1's `PrologueUnitTest` setUp and the behavioral property test place
their fixtures under `HOME` — deliberately outside `/tmp`, to
exercise `build_prologue`'s non-/tmp branch. Under confinement HOME
is swept read-only, so 11 tests errored in setUp the moment the suite
ran inside a sandboxed validation. Fix (in forecast, `tests/`):
`writable_non_tmp_base()` — HOME first (unconfined behavior
unchanged), falling back to **cwd**, which in a confined validation
is staging: writable by construction and outside `/tmp`
(`<repo>/.bale/staging/<sid>`), so the same prologue branch is
exercised. When neither base works the helper raises loudly rather
than skipping — a suite that cannot build a non-/tmp fixture anywhere
means the environment contract broke. Full suite verified **inside**
`run_confined`: 352 tests, OK, 1 capability-gated skip, ~110–122 s.

One boundary worth knowing: with `--staging-dir` pointed *under*
`/tmp` (non-default), a confined suite run has no non-/tmp writable
base at all and those fixtures fail loudly with the explanation. The
default staging location never hits this.

### Checkpoint interaction with the grant (planner decision needed)

The blind checkpoint runs **confined**, under bale-src's own grant
state. Its `run_confined(..., network=True)` probe spins a *nested*
namespace that inherits the checkpoint's own netns — so the
non-loopback visibility assertion can only succeed when the outer
sandbox has network, i.e. **when bale-src's own `bale.toml` carries
`[sandbox] network = true`**, or when the checkpoint capability-gates
the assertion the way the shipped tests do (`/proc/net/dev` of the
invoking environment has a non-`lo` entry → assert; else skip
loudly). Adopting the grant in bale-src's `bale.toml` is a one-line
committed config change on the planner side; I did not make it —
repo-root `bale.toml` policy is the planner's, and this response
already carries three admissions.

## Compaction disclosure (CLAUDE.md §11.6)

The runtime compacted once mid-session, after the probe round and
mid-way through file edits. Disclosed in chat at the point it
happened; recorded here as the durable reference
(`feedback.self_reported.compaction_occurred.disclosure_ref` points
at this section). Recovery per §11.6: re-grounded from the request
manifest and TARBALL.md; every hash in `changes[]` was computed fresh
by `tools/craft_response.py` from the real files (never transcribed
from memory); every claim was re-verified by real runs after
compaction — including the full confined dress rehearsal of
`validation.sh` (exit 0, all claims `[agree]`).

## Design decisions (summary; details ride `feedback.judgment_calls`)

- `[sandbox]` mirrors `[validation]`'s project-only machinery:
  `SANDBOX_VALUES`, a merge branch that drops global `[sandbox]`
  entirely, strict-bool accessor, project-mode wizard walk,
  renderer branch.
- Stamps are unconditional in the attempt builder; the pipeline
  computes them beside the grant resolution
  (`sandbox_escaped = no_sandbox`,
  `network_grant_exercised = grant and not no_sandbox`) and passes
  them at the three validated-attempt sites only — everywhere else
  the false defaults are the honest known-negative.
- `bin/VERSION` is read once at `bin/bale` load; missing and empty
  each fail with the remedy. It is not in build.sh's `EXECUTABLES`.
- New-code comments cite v0.4.5; the drift guard passes at
  `v0.4.5 <= 0.4.5`.

## Verification run here (container, userns available)

- Full suite unconfined: 352 tests OK, ~131 s; sandbox-suite delta
  from this session's additions ≈ **+1.5 s** (target-machine
  baseline 88–89 s → ~90 s, well under the 120 s ceiling).
- Full suite **confined**: 352 tests OK (1 gated skip).
- Real `scripts/build.sh` over the modified tree: pre-flights pass,
  version from `bin/VERSION`, tarball verifies (26 files). Local run
  used a stub `upgrade.sh` (not shipped in context; probe confirmed
  it has no version coupling).
- Install from the built tarball + `validate.sh`: 74/74, including
  the new `bin/VERSION` rows; missing/empty `bin/VERSION` fails
  loudly in both `bale` and `validate.sh`.
- Dress rehearsal of this response's own `validation.sh`, confined,
  over a staged copy with the manifest placed: exit 0, every claim
  reconciles `[agree]`.

## Proposals (prose only)

- **Checkpoint probe surface**: if `current.sh` reads
  `/sys/class/net`, switch it to `/proc/net/dev` (netns-accurate
  through the prologue's fresh proc) and capability-gate the
  non-loopback half unless bale-src adopts the grant. The finding
  above has the empirical detail.
- **bale-src grant adoption**: decide whether bale-src's own
  `bale.toml` sets `[sandbox] network = true`. Its suite does not
  need egress (ADR-0005), so the only pressure is the checkpoint's
  non-loopback probe; gating the probe keeps the repo on the floor.
- **A confined-suite CI leg**: the suite now self-hosts under
  confinement; running it that way routinely (not just at applies)
  would catch the next HOME-shaped assumption before production
  traffic does.


---

# Correction addendum — the HOLD post-mortem (this tarball corrects response-001)

## What the HOLD was

Two independent causes, both visible in the session log:

1. **Suite: 47 E2E failures + 1 error in ~45 s** — every failing test
   spins an inner `bale apply` (a sandbox inside the validation's
   sandbox), and every nested spin died at the prologue:
   `read-only remount failed for /proc/sys/fs/binfmt_misc … not
   mounted`. This tarball fixes it.
2. **Checkpoint FAIL: `network=True still shows loopback-only: grant
   toggle inert`** — this is the first notes' caveat verbatim, not a
   code defect: the checkpoint runs confined under bale-src's own
   grant state, bale-src's `bale.toml` carries no `[sandbox]
   network`, so its nested `run_confined(..., network=True)`
   inherited a loopback-only namespace with nothing beyond `lo` to
   see. (Its floor probe PASSed — the checkpoint's probe surface is
   netns-accurate, so the first notes' sysfs worry does not apply to
   it.) Remedy is one committed line on the planner side — see the
   retry checklist below.

## Probe record 2 (TARBALL.md §4.5)

Paste-back probe `board-10-nesting-hold`, mid-hold. Findings:

- Level-1 confinement works on the target; the level-1 mount table
  shows the inherited `/proc/sys/fs/binfmt_misc binfmt_misc ro`
  entry followed by the prologue's own fresh `/proc proc rw` —
  which SHADOWS it.
- Level-2 spin fails in the prologue with `mount point not mounted`
  for exactly that entry; the self-probe (`ensure_verified`) fails
  the same way at depth 1, which is the suite's one ERROR.
- No userns restrictions on the target (sysctls absent /
  permissive).

## Root cause

The sweep's reachability rule was an existence check (`[ -e
"$target" ]`). A submount shadowed by a later mount over an
**ancestor** path stays listed in the inherited mount table while
its mountpoint directory still exists in the shadowing filesystem —
`/proc/sys/fs/binfmt_misc` is a real procfs directory even when
nothing is mounted there — so the check passed and the remount died
EINVAL. The trigger is the sandbox's own design: the level-1
prologue's fresh `/proc` (step 3, the nestability mount) is what
shadows the binfmt_misc submount that WSL2 always mounts
(Windows-exe interop). My container mounts no binfmt_misc, which is
precisely why the first response's confined, nested dress rehearsal
(353 green) could not surface it — an environment-class gap, owned
in the feedback block.

Reproduced deterministically here before fixing: erecting
`mount tmpfs A; mount tmpfs A/sub; mount --bind src A` (with
`src/sub` existing) produces the byte-identical failure in any
environment.

## The fix (bin/bale_sandbox.py)

Reachability is now the **kernel's** answer, not the mount table's:
an `O_PATH` open of the target, `mnt_id` from
`/proc/self/fdinfo/<fd>`, mapped through `/proc/self/mountinfo` —
the listed target is reachable iff the mount actually containing
the path is one whose mountpoint IS the target. Tool survey in the
reproduced topology (recorded in the module docstring's
alternatives section): `findmnt -T`, `findmnt -M`, and
`mountpoint(1)` are all table-based and report the phantom as
reachable; `st_dev` collides across same-device mounts. The
decision runs as one `python3` annotator pass per spin (python3 is
bale's own hard requirement; measured cost ~50–90 ms, suite delta
nil — the confined full suite actually ran faster than before).

**Fail-closed plumbing**, because the failure direction matters: a
broken annotator must never yield an unswept (writable) tree. Its
output is captured with the exit status checked, an empty
annotation is fatal, any unexpected per-target error raises; only a
can't-open path (the old `[ -e ]` semantics) marks a skip. Skipped
phantoms are logged **by name** (`sweep skipped shadowed
unreachable mount(s): …`), so environment drift stays visible. The
BALE.md §8.5 sentence ("a listed target no path resolves to is
skipped and logged") needed no amendment — the fix implements
"resolves" correctly; mechanism detail lives in the module
docstring per §8.5's ownership rule.

Tests: a regression erects the exact topology (fails on the old
sweep in any environment, passes now with the by-name skip
asserted), and the two S1 shape-pin tests were updated to pin the
new mechanism (annotator, fail-closed capture, `mnt_id`).

## Verification of the correction

- Reproduction: erected topology → old sweep fails byte-identically
  to the target; fixed sweep → rc 0, phantom skipped by name,
  reachable tree still fully swept.
- Level-2 `run_confined` inside `run_confined`: green. Nested
  `ensure_verified` (the ERRORed test's path): green.
- Full suite: **353/353 unconfined (98 s)** and **353/353 inside
  the sandbox (94 s, 1 capability-gated skip)** — nested E2E depth
  exercised throughout.
- `scripts/build.sh` gates green over the corrected tree.

## Retry checklist (operator)

1. **Commit the grant first** (clears the checkpoint's FAIL):
   append to bale-src's `bale.toml` —

       [sandbox]
       network = true

   `git add bale.toml && git commit -m "grant sandbox network
   (ADR-0016 position 3)"`. Retry re-stages from the new tip; the
   provenance stamp covers the checkpoint bytes only, so it still
   verifies. (Alternative if you prefer the floor: capability-gate
   the checkpoint's non-loopback assertion instead; the shipped
   tests show the gate shape.)
2. `bale retry response-001-corrected.tar.gz --allow-out-of-scope
   install.sh --allow-out-of-scope scripts/build.sh
   --allow-out-of-scope validate.sh` — retry never carries
   overrides forward, so all three are re-stated.
3. Expect: checkpoint 8/8, suite 353 green (~60–90 s on your
   hardware), and the applied attempt stamping `sandbox_escaped:
   false, network_grant_exercised: true` — the first exercised
   grant on record.
