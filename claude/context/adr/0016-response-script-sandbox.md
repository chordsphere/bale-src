# ADR-0016: Sandbox bale's execution of response scripts

- **Status:** Accepted
- **Date:** 2026-08-07
- **Supersedes:** —
- **Superseded by:** —

## Context

Every apply executes up to three response-side scripts, and today all
three run the same way: bare `subprocess` with the operator's
privileges, the operator's full inherited environment, network on,
filesystem open — `["bash", <script>]` with `cwd=staging`, nothing
more (`bin/bale_staging.py`: the `apply.sh` invocation in the staging
build, `run_validation_sh`, `run_blind_checkpoint`).

- **`apply.sh`** runs in staging after the `files/` overlay. The
  post-run manifest reconciliation catches undeclared writes *inside*
  the staging tree; nothing catches a write outside it.
- **`validation.sh`** is copied into staging and invoked there,
  network on, filesystem open.
- **The blind checkpoint** is planner-authored, materialized from
  base-tree bytes into a bale-owned tempdir, and invoked down the
  same bare path.

The only pre-flight is `bash -n` on `apply.sh` and `validation.sh`
(`check_response_shell_syntax`) — a syntax gate, not a confinement
one, and the checkpoint doesn't even get that. TARBALL.md §7.1's
"prints every location it will write to" and §9's "never writes
outside staging" are self-declared policy: conventions a
well-behaved script follows, enforced by nothing.

The trust asymmetry is what makes this urgent. Two of the three
scripts are **worker-authored** — the exact artifact the workflow
exists to treat as untrusted-until-validated is handed a bare shell
on the operator's machine as a step of validating it. That is
tolerable precisely while a human reads every script before apply.
The agent-driven direction (ADR-0012) and board 10's unattended
harness end that assumption: an unattended worker's `validation.sh`
runs with nobody reading it first.

ADR-0005 already answered the neighboring question. It sandboxes the
test suite *around* bale — temp `HOME`, temp `BALE_INSTALL`, no
writes to the developer's real environment — under the ethos
"tooling you can run without fear." What it does not cover is bale's
own execution of response scripts at apply time. Same ethos,
uncovered surface. This ADR extends 0005's doctrine to that surface;
it does not restate or modify 0005.

## Decision (proposed — for ratification)

**The ratified floor, carried from the board-10 framing:**
unattended execution requires the sandbox — network off, filesystem
writes confined to staging plus whatever log path bale itself owns
and passes in. This is a non-negotiable prerequisite: board 10's
harness runs no unattended worker before it lands.

On top of that floor, this ADR takes four positions. Each is the
author's craft, flagged for ratification at the master desk.

### 1. Uniform confinement across all three scripts

Confine the checkpoint the same as the worker scripts, not
worker-only. Three grounds:

- **The checkpoint's planner provenance is one merge deep.** It is
  materialized from base-tree bytes — and the base tree is whatever
  the last apply merged. The blindness gate keeps a response from
  smuggling a checkpoint edit into *its own* validation, but an
  admitted change lands in the next session's base tree all the
  same. "Planner-authored" describes the intended authorship, not a
  verified chain of custody.
- **A trust-gradient split means two invocation paths**, and the
  unconfined one is the one exercised least and audited never. One
  wrapper, one code path, tested once, is the simpler mechanism and
  the smaller attack surface.
- **Confinement costs the checkpoint nothing.** By contract, none of
  the three scripts needs network or out-of-tree writes. A sandbox
  that only forbids what the contract already forbids has no
  legitimate victim.

Defense-in-depth wins over trust-gradient here because the gradient
is shallower than it looks.

### 2. Attended path: sandbox default-on, with a per-invocation escape

Once the sandbox lands, it applies to **every** apply — manual
included — not just the unattended harness. The manual workflow is
the fallback and the ground truth (ADR-0012's standing commitments);
a sandbox only the harness exercises is never proven by hand, and
its bugs surface first in an unattended run, which is the worst
possible place. Default-on means every attended apply exercises the
confinement path while a human is watching.

The escape is an explicit **per-invocation** operator flag: loud in
the session log and telemetry, never a config default, never
persistent. It exists for debugging the sandbox itself, not for
routine convenience.

### 3. The network escape hatch: planner-granted, per-project, contract only

Some projects' validation genuinely needs network (dependency-
fetching builds). The grant for those is:

- **planner-granted and per-project** — it lives in planner-
  controlled project configuration, is decided when the project
  adopts the workflow shape, and is recorded in the session log
  whenever it is exercised;
- **never worker-granted** — nothing in a response tarball can
  request, declare, or widen it;
- **scoped, not a bypass** — it relaxes the network leg only;
  filesystem confinement stays intact.

This ADR fixes the contract; the grant's concrete config surface is
the implementation's call.

### 4. Mechanism deferred to board 10

Namespaces, bwrap, containers, seccomp — the implementation chooses,
on board 10, where the build lives. One environment constraint is
recorded here because the implementation inherits it: **the chosen
mechanism must work on WSL**, the architect's standing environment.
A mechanism that is elegant on bare-metal Linux and broken under WSL
fails the manual-path-is-ground-truth commitment on the only machine
the manual path runs on.

### Beyond the floor: environment scrubbing (flagged separately)

The bare subprocess today hands every script the operator's full
inherited environment — including any secrets living in it. Network-
off blunts exfiltration but is not a reason to pass secrets into
untrusted code at all. This ADR proposes the sandbox also reduce the
child environment to a minimal allowlist (what bale itself passes
in, plus what script execution needs: `PATH`, `HOME` as the
mechanism requires, locale). This goes beyond the ratified floor —
ratify or strike it independently of the rest.

## Consequences

- Board 10's unattended-worker gate has its doctrine half; the
  implementation half is unblocked and stays on board 10.
- TARBALL.md §7.1's write-location print and §9's never-outside-
  staging line stop being purely self-declared: the sandbox is their
  mechanical backstop. The declarations stay useful — a declared
  write list reconciled against confined behavior is a better signal
  than either alone.
- The sandbox must preserve the current invocation semantics it
  wraps: `cwd=staging`; the `--verbose` pass-through to
  `validation.sh` (and its deliberate absence for the checkpoint);
  the checkpoint script being *read* from a bale-owned tempdir
  outside staging. Confinement is on writes and network — bale-
  materialized read inputs stay readable.
- Attended applies pick up a mechanism dependency (and its WSL
  quirks). The per-invocation escape is the pressure valve while the
  mechanism matures; its use frequency is itself a telemetry signal
  worth watching.
- Projects with network-dependent validation surface on their first
  sandboxed run as a loud FAIL, and adopt the planner grant
  deliberately rather than relying on ambient network.
- ADR-0005's "tooling you can run without fear" now extends from
  *running the test suite* without fear to *running other parties'
  scripts* without fear — the same doctrine, covering the surface it
  was always pointed at.

## Notes

Extends ADR-0005; modifies nothing in it (append-only, DOCS.md §9).
Authored Proposed per the ADR-0005 precedent — ratification happens
at the master desk, where the four flagged positions and the
environment-scrubbing extension are each accept-or-strike decisions.
The sandbox build itself, and any source changes, are board 10's.

2026-08-07: ratified at the master desk, all five positions including the environment-scrubbing extension; sitting sid 2026-08-07-sandbox-adr-009.
