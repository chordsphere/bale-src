# Response — board-10 S2: network grant, sandbox telemetry, VERSION rider

Session `2026-08-12-board-10-network-grant-001`. Bump 0.4.4 → 0.4.5.

## What landed

1. **Network grant (ADR-0016 position 3).** `bale.toml` gains
   `[sandbox] network` — a boolean, project layer only. The wizard
   walks it in project mode (never `--global`), `merged_config` never
   inherits a global `[sandbox]`, and the accessor is strict-bool
   (a TOML string `"true"` is fatal, never a silent grant). When
   true, apply/retry pass `network=True` to all three confined script
   runs; the sandbox omits its `--net` leg only — filesystem
   confinement and the env scrub are untouched, and the floor stays
   network-off when the key is absent. Grant activation is logged
   (`network GRANTED — bale.toml [sandbox] network`), never
   FORCE-labeled: committed config is not an override.

2. **Sandbox telemetry stamps.** `sandbox_escaped` and
   `network_grant_exercised` — stamped unconditionally by
   `build_telemetry_attempt` on every post-S2 attempt (the
   `overridden_paths` posture: key presence = epoch membership,
   false = known-negative). Real values thread from apply/retry's
   applied/held/reverted sites; an escaped (`--no-sandbox`) apply
   stamps `sandbox_escaped: true` with `network_grant_exercised:
   false` even when the grant is configured — nothing confined ran.
   Schema fields are additive booleans, not in `required`: old
   records keep validating. Write-only; no stats read side.

3. **VERSION rider.** `bin/VERSION` (one line, `0.4.5`) is the
   canonical version. `bin/bale` reads it at load (loud
   missing/empty failures naming the remedy), `scripts/build.sh`
   resolves the release version and the drift guard from it, and
   `validate.sh` reads it for the `--version` cross-check plus a new
   layout row. `bale --version` output is unchanged.

## THIS IS THE CORRECTED TARBALL (post-HOLD)

`corrects` names the held response. One fix rides it:
`bin/bale_sandbox.py`'s read-only sweep now decides reachability
from the kernel (fdinfo `mnt_id`) instead of path existence, so a
submount shadowed by a later mount over an ancestor path — WSL2's
`binfmt_misc` under the prologue's own fresh `/proc`, the cause of
all 47 nested-spin failures — is skipped by name instead of killing
every level-2 sandbox. A regression test erects the exact topology.
The checkpoint's separate FAIL needs one planner-side commit before
retry — see the retry checklist at the end of notes.md, then:

    bale retry response-001-corrected.tar.gz \
      --allow-out-of-scope install.sh \
      --allow-out-of-scope scripts/build.sh \
      --allow-out-of-scope validate.sh

## Applying this response

Three paths sit outside the write forecast (all enumerated in
`feedback.self_reported.forecast_departures` and in notes.md):
`install.sh` and `scripts/build.sh` (the expected VERSION-file
registrations) plus `validate.sh` (probe-confirmed: its version
scrape targets the `VERSION = "…"` line this session removes from
`bin/bale`). The drift gate will name them; admit with:

    bale apply <tarball> \
      --allow-out-of-scope install.sh \
      --allow-out-of-scope scripts/build.sh \
      --allow-out-of-scope validate.sh

`validation.sh` runs the full suite: ~110–130 s on container-class
hardware (352 tests; expect **1 skip** — the non-loopback visibility
assertion capability-gates itself when the validation's own sandbox
has no network, which is exactly the ungranted case).

## Read notes.md before applying

Two first-sandboxed-apply discoveries need your eyes, one of them on
the blind checkpoint's contract: inherited `/sys/class/net` is NOT
netns-accurate inside the sandbox (`/proc/net/dev` is), and the
checkpoint's `network=True` non-loopback assertion can only see
non-loopback interfaces if bale-src's own `bale.toml` carries the
grant (or the checkpoint gates). Details and remedies in notes.md.
