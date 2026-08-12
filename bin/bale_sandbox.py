"""bale_sandbox — namespace confinement for the apply pipeline's response
scripts (ADR-0016, board 10 S1).

Every apply executes up to three response-side scripts — `apply.sh`,
`validation.sh`, and the planner's blind checkpoint — and before this
module they all ran bare: operator privileges, full inherited
environment, network on, filesystem open. ADR-0016 ratified uniform
confinement across all three (the trust gradient between them is one
merge deep), default-on for every apply with a loud per-invocation
escape, plus the environment-scrubbing extension. This module is the
implementation half; the doctrine lives in the ADR.

The mechanism is stdlib Python driving `unshare` from util-linux —
base-system on every target, ratified over bubblewrap (absent on the
architect's WSL environment, and adopting it first requires the
project's how-do-dependencies-live discussion). Inside
`unshare --user --map-root-user --mount --net --pid --fork`, a
generated fixed-shape prologue:

1. marks mount propagation private (`mount --make-rprivate /`);
2. sweeps every mountpoint — deduplicated by target path — with a
   plain per-target `remount,bind,ro`, with no allowlist of skippable
   mounts. Flag preservation is libmount's job, not ours: mount(8)
   merges the topmost mount's current VFS flags into a bind remount
   itself (strace-verified on the build machine and the operator's).
   Restating flags read from findmnt is actively wrong at an
   overmounted path — findmnt lists the shadowed mount too, whose
   flags can differ from the topmost mount the kernel resolves the
   path to, and in a user namespace a mismatched locked flag is
   EPERM (the first target-machine apply HOLDed on exactly this:
   /run/user there is an overmount pair, shadowed noatime under
   topmost relatime). A listed target that does not resolve at all
   (shadowed by an overmount at the same path, or by a later mount
   over an ancestor path — the nested-sandbox case: the level-1
   prologue's fresh /proc shadows an inherited
   /proc/sys/fs/binfmt_misc submount whose mountpoint directory
   still exists, observed on WSL2 at the first sandboxed apply,
   v0.4.5) is skipped and recorded in
   the session log — what no path reaches, the confined child cannot
   write to either; this is a capability rule, not a name allowlist.
   Every reachable target must remount ro or the prologue fails
   loudly (named mount, named error, full findmnt record) so future
   mount-table drift surfaces as a self-probe refusal, not silence;
3. mounts a fresh private `proc` instance (rw — the swept one is ro,
   and a read-only /proc breaks `unshare` inside the sandbox: writing
   `/proc/self/uid_map` is how a nested user namespace maps itself,
   and the blind checkpoint exercising this module as a library runs
   *inside* the sandbox from the first post-landing apply onward);
4. stages a private tmpfs on `/mnt` (an FHS-mandated, always-present
   mountpoint; using it leaves zero residue on the host — the
   original `/mnt` view is restored the instant the move-mount below
   vacates it), populates it with read-only pass-through binds for
   the bale-owned tempdirs that live under `/tmp` (the checkpoint
   materialization dir, the response extraction dir) and read-write
   binds for any handed writable path that lives under `/tmp` (the
   test harness's scratch repos put staging there), then move-mounts
   the tmpfs onto `/tmp`;
5. bind-remounts the handed staging directory and log path (and any
   extra writable paths) read-write at their own locations;
6. uses `-n` on every mount call — the utab update fails once `/run`
   goes read-only;

then `cd`s into staging and `exec`s the wrapped argv. The child
environment is reduced to ENV_ALLOWLIST plus whatever bale itself
deliberately passes — nothing else is inherited (the ratified
environment-scrubbing extension).

The prologue is silent on success: engagement is logged by the caller
(bale), and prologue chatter would pollute the worker script's
captured output, which the TARBALL.md §7.3 reconciliation parse
consumes. On failure it writes one PROLOGUE_FAILURE_SENTINEL-prefixed
line to stderr and exits PROLOGUE_EXIT_CODE (97) — distinguishable
from the wrapped script's own verdict by the sentinel, not by the
exit code alone (a script could legitimately exit 97).

One operational subtlety the sweep imposes, learned in the build
trial: making a mount read-only fails with EBUSY while any file on it
is open for writing, so the confined child must hold no write fds on
swept mounts when the prologue runs. This module's runners capture
output through pipes (never files), and the prologue captures each
mount's stderr via command substitution for the same reason.

Alternatives considered and their re-triggers (recorded here so they
outlive the session that weighed them):

- **Landlock** is the future kernel-native simplification: it would
  replace the owned mount choreography with declarative filesystem
  rules. Re-trigger: kernel >= 6.7 everywhere bale runs AND a wish to
  shed the owned choreography — Landlock's network confinement
  arrives at 6.7, and the architect's standing WSL2 kernel is 6.6.
- **bubblewrap** is the fallback if the owned choreography proves
  more maintenance than it is worth. Re-trigger: recurring
  confinement bugs. Adopting it first requires the project's
  how-do-dependencies-live discussion, which has not happened; the
  architect explicitly declined it for this build.

This module is deliberately standalone — stdlib imports only, no
`__main__` back-references — so the blind checkpoint and the test
suite can import it as a library without bale's CLI in the process.
Imported by `bale_staging` as a sibling module (the `bin/` directory
is on the import path via `bin/bale`'s sys.path prepend), lazily
inside the functions that confine, matching the cluster's convention.
"""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Sequence

# The environment the confined child receives, and nothing else beyond
# what the caller deliberately adds via env_extra (ADR-0016's ratified
# environment-scrubbing extension): PATH and HOME because script
# execution and git need them, locale so tool output is stable.
ENV_ALLOWLIST = ("PATH", "HOME", "LANG", "LC_ALL")

# The unshare invocation the prologue runs under. --user/--map-root-user
# grant mount capability without real privilege; --mount isolates the
# sweep; --net removes network; --pid --fork give the sandbox its own
# pid namespace, which is what entitles the prologue's fresh-proc mount
# (mounting procfs is denied to a user namespace that does not own its
# pid namespace) — and a rw /proc is what keeps confinement nestable.
UNSHARE = "unshare"
UNSHARE_ARGS = ("--user", "--map-root-user", "--mount", "--net",
                "--pid", "--fork")

# NOTE (retry after the first target-machine HOLD): the sweep passes
# plain `remount,bind,ro` and deliberately does NOT restate per-mount
# VFS flags. libmount merges the topmost mount's current flags into a
# bind remount by itself (strace-verified on build and target
# machines); hand-restating flags read from findmnt is wrong at an
# overmounted path, where the listed shadowed mount's flags differ
# from those of the topmost mount the kernel resolves the path to —
# in a user namespace a mismatched locked flag (noatime vs relatime
# on the target machine's /run/user overmount pair) is EPERM.

# The staging mountpoint for the private tmpfs before it move-mounts
# onto /tmp. /mnt is FHS-mandated and exists on every target (WSL
# included); mounting over it briefly shadows its submounts inside the
# namespace only, and the move restores the original view. Chosen over
# a mkdtemp scratch dir because it leaves zero residue on the host.
_TMPFS_STAGE = "/mnt"

PROLOGUE_FAILURE_SENTINEL = "BALE-SANDBOX-PROLOGUE-FAILURE:"
PROLOGUE_EXIT_CODE = 97


class SandboxUnavailableError(RuntimeError):
    """The confinement mechanism does not hold in this environment.

    Raised by verify_confinement / ensure_verified. The message names
    the documented bypass (--no-sandbox) so the refusal is actionable.
    """


def sandbox_env(extra: Optional[dict] = None) -> dict:
    """The scrubbed child environment: ENV_ALLOWLIST from the current
    process env (present keys only), plus `extra` — what bale itself
    deliberately passes. Nothing else is inherited."""
    env = {k: os.environ[k] for k in ENV_ALLOWLIST if k in os.environ}
    if extra:
        env.update(extra)
    return env


def _classify_writable(paths: Sequence[Path]) -> tuple[list[Path], list[Path]]:
    """Split writable paths into (under-/tmp, elsewhere), resolved.

    Under-/tmp writables must ride into the staged tmpfs before the
    move-mount shadows their host location; elsewhere writables get a
    bind-remount,rw at their own path after the sweep.
    """
    under_tmp: list[Path] = []
    elsewhere: list[Path] = []
    for p in paths:
        rp = Path(p).resolve()
        if rp.is_relative_to("/tmp"):
            under_tmp.append(rp)
        else:
            elsewhere.append(rp)
    return under_tmp, elsewhere


def build_prologue(*, staging: Path, log_path: Path,
                   tmp_passthrough: Sequence[Path] = (),
                   extra_writable: Sequence[Path] = ()) -> str:
    """Generate the fixed-shape confinement prologue (module docstring
    steps 1-6) with the handed paths quoted in.

    The shape never varies; only the quoted paths do. Returned as one
    bash script string, executed via `bash -c <prologue> bale-sandbox
    <argv...>` so no temp file is needed — the wrapped argv rides in
    as positional parameters and the prologue ends with `exec "$@"`.
    """
    staging = Path(staging).resolve()
    log_path = Path(log_path).resolve()
    writable_tmp, writable_else = _classify_writable(
        [staging, log_path, *map(Path, extra_writable)])
    ro_tmp = []
    for p in tmp_passthrough:
        rp = Path(p).resolve()
        if rp.is_relative_to("/tmp"):
            ro_tmp.append(rp)
        # A passthrough not under /tmp needs no bind: the ro sweep
        # already leaves it readable at its own path.

    lines = [
        "set -u",
        f'fail() {{ echo "{PROLOGUE_FAILURE_SENTINEL} $*" >&2; '
        f'exit {PROLOGUE_EXIT_CODE}; }}',
        # 1. private propagation, so nothing below leaks to the host.
        'err=$(mount --make-rprivate / 2>&1) || '
        'fail "make-rprivate failed: $err"',
        # 2. the strict ro sweep — every mountpoint, no allowlist,
        # per-mount loud failure. The option string is plain
        # `remount,bind,ro`, exactly what the operator's environment
        # trial attested: libmount merges the topmost mount's current
        # VFS flags into a bind remount itself (verified by strace on
        # both the build and target machines), and restating flags by
        # hand is not just redundant but wrong at an overmounted path —
        # findmnt lists the shadowed mount too, whose flags differ from
        # the topmost mount the kernel actually resolves the path to,
        # and a mismatched locked flag (e.g. noatime vs relatime) is
        # EPERM in a user namespace. Targets are deduplicated for the
        # same reason: N stacked mounts at one path are one reachable
        # mount. Errors are captured via command substitution (a pipe):
        # a redirect to a file would hold a write fd on the very mount
        # being made read-only and EBUSY it.
        #
        # Reachability rule (capability-based, NOT a name allowlist): a
        # listed target that does not resolve TO THAT MOUNT — shadowed
        # by an overmount at the same path, or by a later mount over an
        # ancestor path (its mountpoint directory may still exist in
        # the shadowing filesystem) — is skipped and recorded: what no
        # path resolves to, the confined child cannot write to either.
        # Every reachable target must still remount ro or the prologue
        # fails loudly, with the target's full findmnt record in the
        # sentinel so environment drift self-diagnoses.
        #
        # Reachability is decided by the KERNEL, not the mount table
        # (v0.4.5 fix, first sandboxed apply, WSL2): a submount
        # shadowed by a later mount over an ancestor path is EINVAL
        # ("not mounted") to remount, while its mountpoint directory
        # still exists — canonically, the level-1 prologue's own fresh
        # /proc (step 3) shadows an inherited /proc/sys/fs/binfmt_misc
        # submount, and a level-2 sweep then faced a listed-but-
        # phantom mount and failed loud, breaking nesting. Tool survey
        # in the reproduced topology: findmnt -T, findmnt -M, and
        # mountpoint(1) all answer from the table (longest-prefix
        # entry match) and report the phantom as reachable; st_dev
        # comparison collides across same-device mounts. The kernel's
        # own answer is /proc/self/fdinfo/<fd> mnt_id for an O_PATH
        # open of the target, mapped through /proc/self/mountinfo:
        # reachable iff the mount actually containing the path is one
        # whose mountpoint IS the target. One python3 pass annotates
        # every findmnt line R/S (python3 is bale's own hard
        # requirement, so the prologue may lean on it).
        #
        # Fail-closed plumbing, because the failure direction matters:
        # a broken annotator must never yield an unswept (writable)
        # tree. Output is captured with the exit status checked, an
        # empty annotation is fatal (a real mount table is never
        # empty), any unexpected per-target error raises inside the
        # annotator (only a can't-open path — the old [ -e ] rule —
        # marks S), and the raw escaped target text passes through
        # untouched so the shell's %b stays the single decode point.
        'BALE_REACH_PY=$(cat <<"BALE_REACH_EOF"',
        "import os, sys",
        "mounts = {}",
        'with open("/proc/self/mountinfo") as fh:',
        "    for line in fh:",
        '        f = line.split(" ")',
        "        mounts[f[0]] = f[4]",
        "def unesc(s):",
        '    return bytes(s, "utf-8").decode("unicode_escape")',
        "out = []",
        "for raw in sys.stdin.read().splitlines():",
        "    if not raw:",
        "        continue",
        "    t = unesc(raw)",
        '    mark = "S"',
        "    fd = -1",
        "    try:",
        "        fd = os.open(t, os.O_PATH)",
        "    except OSError:",
        "        fd = -1",
        "    if fd >= 0:",
        "        try:",
        "            mnt_id = None",
        '            with open("/proc/self/fdinfo/%d" % fd) as fh:',
        "                for l in fh:",
        '                    if l.startswith("mnt_id:"):',
        "                        mnt_id = l.split()[1]",
        "                        break",
        "            if mnt_id is None:",
        "                raise RuntimeError(",
        '                    "no mnt_id in fdinfo - cannot decide '
        'reachability")',
        "            mp = mounts.get(mnt_id)",
        "            if mp is not None and unesc(mp) == t:",
        '                mark = "R"',
        "        finally:",
        "            os.close(fd)",
        '    out.append(mark + "|" + raw)',
        'sys.stdout.write("\\n".join(out) + "\\n")',
        "BALE_REACH_EOF",
        ")",
        'entries=$(findmnt -rn -o TARGET | python3 -c "$BALE_REACH_PY")'
        ' || fail "sweep reachability annotator failed — refusing an '
        'unswept tree"',
        '[ -n "$entries" ] || fail "sweep reachability annotator '
        'produced no entries — refusing an unswept tree"',
        'swept=""',
        'skipped=""',
        "while IFS= read -r entry; do",
        '  mark=${entry%%|*}',
        '  target=${entry#*|}',
        "  target=$(printf '%b' \"$target\")",
        '  case ",$swept," in *",$target,"*) continue;; esac',
        '  swept="$swept,$target"',
        '  if [ "$mark" != "R" ]; then skipped="$skipped $target"; '
        "continue; fi",
        '  err=$(mount -n -o remount,bind,ro "$target" 2>&1) || '
        'fail "read-only remount failed for $target: $err'
        ' [findmnt: $(findmnt -rn -o TARGET,FSTYPE,VFS-OPTIONS,FS-OPTIONS,'
        'PROPAGATION "$target" 2>&1 | tr "\\n" ";")]"',
        'done <<< "$entries"',
        # 3. fresh rw proc — the swept instance is ro, and confinement
        # must stay nestable (module docstring).
        'err=$(mount -n -t proc proc /proc 2>&1) || '
        'fail "fresh /proc mount failed: $err"',
        # 4. private tmpfs staged on /mnt, populated, moved onto /tmp.
        f'err=$(mount -n -t tmpfs -o mode=1777 tmpfs {_TMPFS_STAGE} 2>&1)'
        ' || fail "tmpfs stage failed: $err"',
    ]
    for p in ro_tmp:
        rel = p.relative_to("/tmp")
        dst = shlex.quote(f"{_TMPFS_STAGE}/{rel}")
        src = shlex.quote(str(p))
        lines += [
            f"mkdir -p {dst}",
            f'err=$(mount -n --bind {src} {dst} 2>&1) || '
            f'fail "pass-through bind failed for {src}: $err"',
            f'err=$(mount -n -o remount,bind,ro {dst} 2>&1) || '
            f'fail "pass-through ro remount failed for {src}: $err"',
        ]
    for p in writable_tmp:
        rel = p.relative_to("/tmp")
        dst = shlex.quote(f"{_TMPFS_STAGE}/{rel}")
        src = shlex.quote(str(p))
        # A writable file (the log path) needs an existing file as the
        # bind target; a directory needs a directory.
        lines += [
            f"if [ -d {src} ]; then mkdir -p {dst}; "
            f"else mkdir -p $(dirname {dst}) && : > {dst}; fi",
            f'err=$(mount -n --bind {src} {dst} 2>&1) || '
            f'fail "writable bind failed for {src}: $err"',
            f'err=$(mount -n -o remount,bind,rw {dst} 2>&1) || '
            f'fail "writable remount failed for {src}: $err"',
        ]
    lines.append(
        f'err=$(mount -n --move {_TMPFS_STAGE} /tmp 2>&1) || '
        'fail "move-mount onto /tmp failed: $err"')
    # 5. rw binds at their own paths for non-/tmp writables.
    for p in writable_else:
        q = shlex.quote(str(p))
        lines += [
            f'err=$(mount -n --bind {q} {q} 2>&1) || '
            f'fail "writable bind failed for {q}: $err"',
            f'err=$(mount -n -o remount,bind,rw {q} 2>&1) || '
            f'fail "writable remount failed for {q}: $err"',
        ]
    st = shlex.quote(str(staging))
    lg = shlex.quote(str(log_path))
    lines += [
        # Skipped shadowed targets are recorded in the session log —
        # now writable — not stdout/stderr: the prologue stays silent
        # on success so confined script output remains clean for the
        # TARBALL.md 7.3 reconciliation parse.
        'if [ -n "$skipped" ]; then '
        'echo "[bale-sandbox] sweep skipped shadowed unreachable '
        f'mount(s):$skipped" >> {lg} 2>/dev/null || true; fi',
        f'cd {st} || fail "cd into staging {st} failed"',
        'exec "$@"',
    ]
    return "\n".join(lines) + "\n"


def confined_command(argv: Sequence[str], *, staging: Path,
                     log_path: Path,
                     tmp_passthrough: Sequence[Path] = (),
                     extra_writable: Sequence[Path] = (),
                     network: bool = False) -> list[str]:
    """The full subprocess argv: unshare + prologue + the wrapped argv.

    `network=True` omits --net from the unshare flags — the leg the
    planner-granted network relaxation drives (ADR-0016 position 3;
    since v0.4.5, board 10 S2, bale passes it when the project's
    bale.toml [sandbox] network grant is set). The filesystem
    confinement is identical either way.
    """
    flags = [f for f in UNSHARE_ARGS if not (network and f == "--net")]
    prologue = build_prologue(
        staging=staging, log_path=log_path,
        tmp_passthrough=tmp_passthrough, extra_writable=extra_writable)
    return [UNSHARE, *flags, "bash", "-c", prologue,
            "bale-sandbox", *argv]


def _prepare(staging: Path, log_path: Path) -> None:
    """Parent-side pre-flight: the bind targets must exist."""
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if not log_path.exists():
        log_path.touch()
    if not Path(staging).is_dir():
        raise RuntimeError(
            f"sandbox staging directory does not exist: {staging}")


def popen_confined(argv: Sequence[str], *, staging: Path, log_path: Path,
                   tmp_passthrough: Sequence[Path] = (),
                   extra_writable: Sequence[Path] = (),
                   env_extra: Optional[dict] = None,
                   network: bool = False,
                   **popen_kwargs) -> subprocess.Popen:
    """Confined subprocess.Popen — for callers that stream output live.

    Output should be captured through pipes only: an inherited write
    fd to a file on a swept mount EBUSYs the sweep (module docstring).
    cwd is set inside the namespace by the prologue's own `cd`; the
    parent-side cwd is set to staging too so pre-exec relative
    resolution matches.
    """
    _prepare(staging, log_path)
    cmd = confined_command(argv, staging=staging, log_path=log_path,
                           tmp_passthrough=tmp_passthrough,
                           extra_writable=extra_writable, network=network)
    return subprocess.Popen(cmd, cwd=str(staging),
                            env=sandbox_env(env_extra), **popen_kwargs)


def run_confined(argv: Sequence[str], *, staging: Path, log_path: Path,
                 tmp_passthrough: Sequence[Path] = (),
                 extra_writable: Sequence[Path] = (),
                 env_extra: Optional[dict] = None,
                 network: bool = False,
                 capture_output: bool = True,
                 text: bool = True) -> subprocess.CompletedProcess:
    """Run `argv` confined; return the CompletedProcess.

    The pinned S1 surface (board 10): `argv` positional; `staging` and
    `log_path` required keywords; the return value carries
    `.returncode`. Writes land only in `staging`, `log_path`, and any
    `extra_writable` path; the network is off unless `network=True`
    (the ADR-0016 position-3 grant leg — filesystem confinement is
    unchanged by it); the child environment
    is ENV_ALLOWLIST plus `env_extra`. A prologue failure surfaces as
    PROLOGUE_EXIT_CODE with a PROLOGUE_FAILURE_SENTINEL line on
    stderr — the sentinel, not the exit code, is the discriminator.
    """
    _prepare(staging, log_path)
    cmd = confined_command(argv, staging=staging, log_path=log_path,
                           tmp_passthrough=tmp_passthrough,
                           extra_writable=extra_writable, network=network)
    return subprocess.run(cmd, cwd=str(staging),
                          env=sandbox_env(env_extra),
                          capture_output=capture_output, text=text)


# --- self-probe -----------------------------------------------------------

# The probe script asserts the four properties the confinement contract
# promises (and the blind checkpoint independently probes): an
# in-staging write succeeds, an outside write is denied, the network is
# off, and a canary exported by the operator's environment is invisible.
# Each violation prints its own line so a refusal names what failed.
_PROBE_CANARY = "BALE_SANDBOX_PROBE_CANARY"
_PROBE_SCRIPT = """
set -u
ok=0
echo probe > .sandbox-probe-write || { echo "PROBE-FAIL: in-staging write denied"; ok=1; }
if echo x > "$1" 2>/dev/null; then echo "PROBE-FAIL: outside write landed at $1"; ok=1; fi
if (exec 3<>/dev/tcp/127.0.0.1/9) 2>/dev/null; then echo "PROBE-FAIL: network reachable"; ok=1; fi
if [ -n "${%(canary)s:-}" ]; then echo "PROBE-FAIL: operator environment leaked (%(canary)s visible)"; ok=1; fi
exit $ok
""" % {"canary": _PROBE_CANARY}

_verified = False


def verify_confinement(log_path: Path, *, probe_dir: Path) -> None:
    """Run the self-probe once: spin the namespace against `probe_dir`
    as staging and assert the confinement properties hold.

    Raises SandboxUnavailableError — naming --no-sandbox as the
    documented bypass — when the namespace cannot spin, the prologue's
    strict sweep refuses (its per-mount loud failure is this probe's
    substrate: mount-table drift surfaces here, named), or any probed
    property is violated. Never falls back to unconfined execution.
    """
    # The outside-write target must sit on a swept host mount. A path
    # derived from probe_dir can resolve inside the sandbox's private
    # /tmp tmpfs (whose scaffolding is writable by design — writes
    # there are ephemeral and never reach the host), which would
    # misread the feature as a breach. /usr is FHS-mandated, always
    # host-backed, and always in the sweep.
    outside = "/usr/.bale-sandbox-probe-escape"
    os.environ[_PROBE_CANARY] = "leak-check"
    try:
        try:
            result = run_confined(
                ["bash", "-c", _PROBE_SCRIPT, "sandbox-probe", outside],
                staging=probe_dir, log_path=log_path)
        except OSError as e:
            raise SandboxUnavailableError(
                f"sandbox self-probe could not launch unshare: {e}. "
                f"Scripts will not run unconfined silently; the "
                f"documented bypass is --no-sandbox (per invocation, "
                f"FORCE-logged).")
    finally:
        os.environ.pop(_PROBE_CANARY, None)
    if result.returncode != 0:
        detail = "\n".join(
            s for s in (result.stdout, result.stderr) if s and s.strip())
        raise SandboxUnavailableError(
            f"sandbox self-probe failed (exit {result.returncode}) — the "
            f"confinement mechanism does not hold in this environment:\n"
            f"{detail.strip()}\n"
            f"Scripts will not run unconfined silently; the documented "
            f"bypass is --no-sandbox (per invocation, FORCE-logged).")


def ensure_verified(log_path: Path) -> None:
    """Run the self-probe at first use in this process; cached after.

    One probe per apply (the pipeline is one process), before the
    first confined script runs — ADR-0016's refusal contract: on
    failure, a loud SandboxUnavailableError naming the escape flag,
    never silent unconfined execution. The probe scratch lives under
    the log directory (inside `.bale/`, which every reconciliation
    walk skips) and is removed on the way out.
    """
    global _verified
    if _verified:
        return
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    probe_dir = Path(tempfile.mkdtemp(prefix="sandbox-probe-",
                                      dir=log_path.parent))
    try:
        verify_confinement(log_path, probe_dir=probe_dir)
    finally:
        shutil.rmtree(probe_dir, ignore_errors=True)
    _verified = True
