"""bale_open — the `bale open <bundle>` verb (board 49a-ii, v0.4.13).

Consumes a planner bundle (format home: BALE.md §6.7, landed by the
49a-i seam) and turns it into a packed session in one paste: the
operator saves one `.bale-bundle` file and pastes one desk-emitted
`bale open` line — the paste-block-surface contract — and this module
does everything the old ceremony spread across hand-typed steps:

1. **Gate the bundle before anything else is trusted.** Extract
   `bundle.json`, LF-normalize it, and run it through
   `validate_bundle_manifest` (bin/bale_validate.py) — the 49a-i
   transported consumer contract. A bundle whose manifest fails the
   gate refuses before any member is read.
2. **Verify both member hashes** (boards 36 and 40, absorbed): each
   present member's LF-normalized bytes must hash to the manifest's
   published sha256. The archive is sealed — an undeclared member, or
   a declared member missing from the archive, refuses.
3. **Dry-run the checkpoint read-only against the live base** (board
   48's leg, subsumed): the extracted checkpoint executes against a
   scratch copy of the live working tree — the live tree is untouched
   by construction — confined by default (ADR-0016 uniform posture),
   and the named probes' verdict lines are echoed as the
   **expected-HOLD proof**: exit 1 (probes FAIL pre-work) is the
   expected outcome and proves the oracle grades real, not-yet-landed
   work; exit 2 (the oracle itself errored) refuses the whole open as
   a defective oracle before any session state exists; exit 0 (the
   oracle passes before any work landed) proceeds with a loud
   vacuous-oracle warning — the row ratifies only the exit-2 refusal,
   and an all-invariant checkpoint is the planner's call to make.
4. **Replay the pack argv** with delivery-flag injection: the stored
   `pack_argv` never carries `--readme-file`/`--checkpoint-file`
   (validate_bundle_manifest refuses a stored one); this module
   appends them pointing at the extracted members — `--no-readme`
   when the brief slot is an explicit null — so member presence is
   the single source for flag injection. The bundle's `pre_answered`
   intents ride in on the in-process channel (the `pre_answered`
   namespace attribute cmd_pack reads; BALE.md §6.7 — no CLI flag
   can spell one), routed *through* every decline-default exchange,
   never around it.

Sibling-module conventions match the cluster (bale_pack, bale_apply):
bin/bale-owned shared helpers (fail, log, repo_root,
resolve_inbound_path, build_parser) are imported lazily from
__main__ inside the functions that need them; sibling-owned entry
points come from their owning modules. Dependency direction: bin/bale
imports this module; this module reaches into bale_pack for the
recognizer/intents surface and into bale_validate for the manifest
gate, and never into bale_apply.

Sections:
  1. Line-ending normalization        (~line 70)
  2. Bundle extraction + verification (~line 95)
  3. Checkpoint dry-run               (~line 285)
  4. Argv replay + cmd_open           (~line 470)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# 1. Line-ending normalization
# ---------------------------------------------------------------------------

def normalize_bundle_member(data: bytes) -> bytes:
    """Return `data` with every CRLF read as LF (BALE.md §6.7).

    The bundle format's own normalization rule: member hashes are
    computed over, and verified against, LF-normalized bytes, so a
    bundle that traveled a line-ending-mangling transport (mail, chat,
    a Windows checkout) still verifies. Scoped to bundle reads — this
    is not board 50's repo-wide CRLF tolerance, and nothing outside
    this module should call it for non-bundle bytes.
    """
    return data.replace(b"\r\n", b"\n")


# ---------------------------------------------------------------------------
# 2. Bundle extraction + verification
# ---------------------------------------------------------------------------

BUNDLE_MANIFEST_NAME = "bundle.json"

# The checkpoint script contract (board-6 revB, D2; TARBALL.md §7.5):
# 0 = every probe passed, 1 = at least one probe failed, 2 = the
# script itself errored. The dry-run inherits these read-only.
_CHECKPOINT_PASS = 0
_CHECKPOINT_HOLD = 1

# Probe-verdict grammar the proof echo keys on — one line per probe,
# the same [PASS]/[FAIL]/[SKIP] vocabulary validation.sh uses.
_PROBE_PREFIXES = ("[PASS]", "[FAIL]", "[SKIP]")


def _flat_member_name_or_none(member: tarfile.TarInfo) -> Optional[str]:
    """Return the member's flat root-level name, or None when the
    member is anything a sealed bundle cannot carry.

    Members sit flat at the archive root (BALE.md §6.7): a regular
    file whose name has no path separators and is not '.' or '..'.
    A leading './' (some tar writers prefix it) is tolerated and
    stripped — the name underneath must still be flat. Directories,
    links, devices, and nested paths all return None; the caller
    refuses on any None, naming the member.
    """
    if not member.isreg():
        return None
    name = member.name
    if name.startswith("./"):
        name = name[2:]
    if not name or name in (".", "..") or "/" in name or "\\" in name:
        return None
    return name


def read_bundle(bundle_path: Path) -> tuple[dict, dict[str, bytes]]:
    """Open, gate, and verify a planner bundle; return
    (manifest, {member_name: normalized_bytes}).

    The full consumption contract of BALE.md §6.7's container, run in
    trust order — nothing later is touched until everything earlier
    held:

    1. the archive lists only flat regular files, `bundle.json` among
       them;
    2. `bundle.json` (LF-normalized) parses as JSON and passes
       `validate_bundle_manifest` — the gate before anything else in
       the bundle is trusted (the 49a-i transported contract; this
       covers bundle_format == 1, so an unrecognized version refuses
       here rather than being guessed at);
    3. the archive's member set equals {bundle.json} ∪ the declared
       member paths exactly — an undeclared member refuses (a bundle
       is a sealed artifact, not a container format), and a declared
       member missing from the archive refuses;
    4. each declared member's LF-normalized bytes hash to the
       manifest's published sha256 (boards 36 and 40) — a mismatch
       refuses, naming the member and both digests.

    Returns the parsed manifest and the extracted members keyed by
    their flat archive names, values already LF-normalized (the bytes
    the hashes vouch for are the bytes every downstream consumer —
    the dry-run, the delivery flags — gets). All extraction is
    in-memory (`extractfile`), so no tar path-handling quirk can
    write outside the process.

    Refusals go through __main__.fail — this function is a CLI leg,
    not a library surface; validate_bundle_manifest remains the
    library entry point for manifest-only checks.
    """
    from __main__ import fail  # lazy — see module docstring
    from bale_validate import validate_bundle_manifest  # lazy — sibling

    try:
        tf = tarfile.open(bundle_path, mode="r:gz")
    except (tarfile.TarError, OSError) as e:
        fail(f"could not open {bundle_path} as a gzipped tar: {e} — a "
             f"planner bundle is a gzipped tar with members flat at the "
             f"archive root (BALE.md \u00a76.7)")
    with tf:
        names: dict[str, tarfile.TarInfo] = {}
        for member in tf.getmembers():
            flat = _flat_member_name_or_none(member)
            if flat is None:
                fail(f"bundle member {member.name!r} is not a flat "
                     f"regular file at the archive root — a planner "
                     f"bundle carries only flat file members "
                     f"(BALE.md \u00a76.7); refusing the sealed-artifact "
                     f"violation")
            if flat in names:
                fail(f"bundle member {flat!r} appears twice in the "
                     f"archive — refusing the ambiguity")
            names[flat] = member

        if BUNDLE_MANIFEST_NAME not in names:
            fail(f"bundle has no {BUNDLE_MANIFEST_NAME} at the archive "
                 f"root — not a planner bundle (BALE.md \u00a76.7)")

        raw = tf.extractfile(names[BUNDLE_MANIFEST_NAME])
        assert raw is not None  # isreg() checked above
        manifest_bytes = normalize_bundle_member(raw.read())
        try:
            manifest = json.loads(manifest_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            fail(f"{BUNDLE_MANIFEST_NAME} is not valid UTF-8 JSON: {e}")

        errors = validate_bundle_manifest(manifest)
        if errors:
            listed = "\n".join(f"  - {e}" for e in errors)
            fail(f"bundle manifest failed validation "
                 f"({len(errors)} error(s)):\n{listed}\n"
                 f"The bundle is gated before anything else in it is "
                 f"trusted (BALE.md \u00a76.7); nothing was extracted "
                 f"and no session state exists.")

        # Declared member set — both slots are always present in a
        # valid manifest, each an object or an explicit null.
        declared: dict[str, dict] = {}
        for slot in ("brief", "checkpoint"):
            entry = manifest["members"][slot]
            if entry is not None:
                declared[entry["path"]] = entry

        expected = {BUNDLE_MANIFEST_NAME} | set(declared)
        undeclared = sorted(set(names) - expected)
        if undeclared:
            fail(f"bundle carries member(s) the manifest does not "
                 f"declare: {', '.join(repr(n) for n in undeclared)} — "
                 f"a bundle is a sealed artifact, not a container "
                 f"format (BALE.md \u00a76.7); unknown members refuse")
        missing = sorted(set(declared) - set(names))
        if missing:
            fail(f"bundle manifest declares member(s) the archive does "
                 f"not carry: {', '.join(repr(n) for n in missing)}")

        members: dict[str, bytes] = {}
        for name, entry in declared.items():
            raw = tf.extractfile(names[name])
            assert raw is not None
            data = normalize_bundle_member(raw.read())
            digest = hashlib.sha256(data).hexdigest()
            if digest != entry["sha256"]:
                fail(f"bundle member {name!r} failed hash "
                     f"verification: the manifest publishes "
                     f"{entry['sha256']} but the member's "
                     f"LF-normalized bytes hash to {digest} — the "
                     f"bundle's content does not match what the desk "
                     f"published (boards 36/40; BALE.md \u00a76.7). "
                     f"Nothing proceeds on unverified bytes.")
            members[name] = data

    return manifest, members


# ---------------------------------------------------------------------------
# 3. Checkpoint dry-run
# ---------------------------------------------------------------------------

def _copy_live_base(repo: Path, dest: Path) -> None:
    """Copy the live working tree (`.git` included, `.bale/` excluded)
    into `dest`.

    The dry-run's read-only guarantee is structural: the checkpoint
    executes against this scratch copy, so the live base cannot be
    written no matter what the script does — the same containment
    posture as apply's working-tree staging (bale_staging), rebuilt
    here because no session and no staging layout exist yet at open
    time. `.git` rides along so git-based probes see the real
    history; `.bale/` stays behind — it is bale's own state dir, holds
    the staging root, and no checkpoint probe may depend on it.
    """
    def _ignore(dirpath, entries):
        if Path(dirpath).resolve() == repo.resolve():
            return [e for e in entries if e == ".bale"]
        return []

    shutil.copytree(repo, dest, symlinks=True, ignore=_ignore)


def _echo_hold_proof(output: str, exit_code: int) -> None:
    """Echo the named probes' verdict lines — the expected-HOLD proof.

    The proof's value is the operator *seeing* named probes execute
    against real bytes (row 49's dry-run leg), so the probe-grammar
    lines ([PASS]/[FAIL]/[SKIP]) print verbatim; everything else in
    the captured output is summarized to a count and kept in the
    session-adjacent log the caller wrote. Verbose mode streams the
    whole run live and never reaches here.
    """
    from __main__ import log  # lazy — see module docstring
    probe_lines = [ln for ln in output.splitlines()
                   if ln.lstrip().startswith(_PROBE_PREFIXES)]
    other = len(output.splitlines()) - len(probe_lines)
    log(f"checkpoint dry-run probes ({len(probe_lines)} verdict "
        f"line(s), {other} other output line(s) in the log):")
    for ln in probe_lines:
        print(f"    {ln}")
    log(f"checkpoint dry-run exit code: {exit_code}")


def dry_run_checkpoint(repo: Path, script_bytes: bytes, member_name: str,
                       *, log_path: Path, verbose: bool,
                       sandbox: bool, network: bool) -> int:
    """Execute the bundle's checkpoint read-only against the live base;
    return the script's exit code.

    Board 48's leg, subsumed into row 49: the extracted (already
    LF-normalized, hash-verified) checkpoint bytes run against a
    scratch copy of the live working tree — read-only w.r.t. the real
    tree by construction (_copy_live_base) — under the same
    confinement the apply-time run gets (ADR-0016 position 1: uniform
    confinement; `sandbox=False` is the caller's FORCE-logged escape,
    `network` is the position-3 grant threaded verbatim). Invocation
    mirrors run_blind_checkpoint (bale_staging): interpreter
    invocation (`bash <script>`) plus an explicit exec bit, the
    materialization tempdir passed through read-only, output captured
    (or streamed under `verbose`) and appended to `log_path` in a
    banded section so the proof survives the console.

    Exit-code interpretation is the caller's (cmd_open) — this
    function runs and records, the caller judges, the same split
    run_blind_checkpoint keeps with apply's PASS/HOLD derivation.
    """
    from __main__ import log  # lazy — see module docstring
    if sandbox:
        import bale_sandbox  # lazy — sibling module, standalone by design
        from __main__ import fail

    base_dir = Path(tempfile.mkdtemp(prefix="bale-open-base-"))
    script_dir = Path(tempfile.mkdtemp(prefix="bale-open-checkpoint-"))
    try:
        scratch = base_dir / "base"
        _copy_live_base(repo, scratch)
        script = script_dir / Path(member_name).name
        script.write_bytes(script_bytes)
        script.chmod(0o755)

        script_sha = hashlib.sha256(script_bytes).hexdigest()
        log(f"dry-running bundle checkpoint {member_name} "
            f"({script_sha[:12]}) read-only against a scratch copy of "
            f"the live base"
            + ((", confined"
                + (", network GRANTED — bale.toml [sandbox] network"
                   if network else ""))
               if sandbox else ", UNCONFINED — --no-sandbox")
            + (" (verbose: streaming live)..." if verbose else "..."))

        log_path.parent.mkdir(parents=True, exist_ok=True)
        band = (f"=== bundle checkpoint dry-run ({member_name}, "
                f"{script_sha[:12]}) ===")

        if sandbox:
            try:
                bale_sandbox.ensure_verified(log_path)
            except bale_sandbox.SandboxUnavailableError as e:
                fail(str(e))

        if verbose:
            if sandbox:
                proc = bale_sandbox.popen_confined(
                    ["bash", str(script)],
                    staging=scratch, log_path=log_path,
                    tmp_passthrough=[script_dir],
                    network=network,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True, bufsize=1,
                )
            else:
                proc = subprocess.Popen(
                    ["bash", str(script)],
                    cwd=str(scratch),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True, bufsize=1,
                )
            collected: list[str] = []
            assert proc.stdout is not None
            for line in proc.stdout:
                sys.stdout.write(line)
                sys.stdout.flush()
                collected.append(line)
            returncode = proc.wait()
            merged = "".join(collected)
            stderr_text = ""
        else:
            if sandbox:
                result = bale_sandbox.run_confined(
                    ["bash", str(script)],
                    staging=scratch, log_path=log_path,
                    tmp_passthrough=[script_dir],
                    network=network,
                )
            else:
                result = subprocess.run(
                    ["bash", str(script)],
                    cwd=str(scratch),
                    capture_output=True, text=True,
                )
            returncode = result.returncode
            merged = result.stdout
            stderr_text = result.stderr or ""

        with log_path.open("a", encoding="utf-8") as f:
            f.write(f"\n{band}\n")
            f.write(merged)
            if stderr_text:
                f.write("\n--- dry-run stderr ---\n")
                f.write(stderr_text)
            f.write(f"\n--- dry-run exit code: {returncode} ---\n")

        if sandbox and returncode == getattr(
                sys.modules.get("bale_sandbox"), "PROLOGUE_EXIT_CODE", 97):
            import bale_sandbox as _sb
            if _sb.PROLOGUE_FAILURE_SENTINEL in stderr_text:
                from __main__ import fail as _fail
                _fail(f"the sandbox prologue failed before the "
                      f"checkpoint ran: "
                      f"{stderr_text.strip().splitlines()[-1]} — this "
                      f"is a confinement failure, not a checkpoint "
                      f"verdict; --no-sandbox is the debugging escape "
                      f"(ADR-0016)")

        if not verbose:
            _echo_hold_proof(merged + (("\n" + stderr_text)
                                       if stderr_text else ""),
                             returncode)
        else:
            log(f"checkpoint dry-run exit code: {returncode}")
        return returncode
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)
        shutil.rmtree(script_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# 4. Argv replay + cmd_open
# ---------------------------------------------------------------------------

def compose_pack_argv(manifest: dict, extracted: dict[str, Path]) -> list[str]:
    """Return the full `pack` argv: the stored vector plus the injected
    delivery flags.

    The stored `pack_argv` is the argument vector AFTER the `pack`
    subcommand and never carries a delivery flag
    (validate_bundle_manifest refused a stored one before this runs);
    injection follows member presence — the single source, so the
    replayed invocation can never disagree with the shipped bytes
    (BALE.md §6.7): `--readme-file <extracted brief>` when the brief
    member ships, `--no-readme` when the slot is an explicit null, and
    `--checkpoint-file <extracted checkpoint>` when the checkpoint
    member ships. Extracted paths are absolute, bypassing
    resolve_inbound_path's search by that function's own contract.
    """
    argv = ["pack"] + list(manifest["pack_argv"])
    brief = manifest["members"]["brief"]
    if brief is not None:
        argv += ["--readme-file", str(extracted[brief["path"]])]
    else:
        argv += ["--no-readme"]
    checkpoint = manifest["members"]["checkpoint"]
    if checkpoint is not None:
        argv += ["--checkpoint-file", str(extracted[checkpoint["path"]])]
    return argv


def cmd_open(args: argparse.Namespace) -> int:
    """`bale open <bundle>` — verify, dry-run, replay (board 49a-ii).

    The pipeline, in trust order; every refusal happens before any
    session state exists:

    1. resolve the bundle argument (apply's search-path semantics,
       kind "bundle"); refuse a file outside the reserved suffix —
       the suffix IS the recognizer (BALE.md §6.7);
    2. read_bundle(): gate the manifest, seal-check the archive,
       verify both member hashes;
    3. when the checkpoint member ships: refuse up front if the
       project pins no [validation] base (the same refusal
       `--checkpoint-file` would give, moved before the dry-run's
       cost), then dry-run it read-only against the live base and
       judge the exit code — 1 is the expected-HOLD proof, 0
       proceeds with a loud vacuous-oracle warning, anything else
       refuses the open as a defective oracle;
    4. echo and replay the composed pack invocation through the real
       CLI parser with the bundle's `pre_answered` intents on the
       namespace (the in-process channel; BALE.md §6.7), returning
       cmd_pack's own exit code.
    """
    from __main__ import (  # lazy — see module docstring
        build_parser,
        fail,
        log,
        repo_root,
        resolve_inbound_path,
    )
    import bale_config  # lazy — sibling module
    from bale_pack import BUNDLE_SUFFIX, is_bundle_file  # lazy — sibling

    cwd = Path.cwd().resolve()
    repo = repo_root(cwd)
    if repo is None:
        fail("bale open runs inside the project repository: the "
             "checkpoint dry-run executes against the live base, and "
             "the replayed pack targets this repo. cd into the project "
             "and re-run.")

    cfg = bale_config.merged_config(repo)
    search_paths = bale_config.get_apply_search_paths(cfg)
    bundle_path = resolve_inbound_path(args.bundle, cwd, search_paths,
                                       kind="bundle")
    if not bundle_path.is_file():
        fail(f"bundle not found: {bundle_path}")
    if not is_bundle_file(bundle_path.name):
        fail(f"{bundle_path.name!r} does not carry the reserved "
             f"planner-bundle suffix {BUNDLE_SUFFIX!r} — the suffix is "
             f"the recognizer (BALE.md \u00a76.7), and bale open "
             f"consumes only planner bundles.")

    log(f"opening planner bundle {bundle_path}")
    manifest, members = read_bundle(bundle_path)

    brief = manifest["members"]["brief"]
    checkpoint = manifest["members"]["checkpoint"]
    for slot, entry in (("brief", brief), ("checkpoint", checkpoint)):
        if entry is None:
            log(f"member {slot}: explicit null (not shipped)")
        else:
            log(f"member {slot} verified: {entry['path']} "
                f"(sha256 {entry['sha256'][:12]}\u2026, LF-normalized)")

    # Extract verified members to a tempdir that outlives the replayed
    # pack — cmd_pack reads the delivery-flag files during its own run.
    extract_dir = Path(tempfile.mkdtemp(prefix="bale-open-members-"))
    try:
        extracted: dict[str, Path] = {}
        for name, data in members.items():
            target = extract_dir / name
            target.write_bytes(data)
            extracted[name] = target

        if checkpoint is not None:
            if bale_config.get_validation_base(cfg) is None:
                fail(f"the bundle ships a checkpoint member "
                     f"({checkpoint['path']}) but this project pins no "
                     f"[validation] base in bale.toml — the replayed "
                     f"pack's --checkpoint-file would refuse for the "
                     f"same reason. Configure [validation] base (see "
                     f"`bale config init`), or use a bundle authored "
                     f"for an oracle-less project.")
            network = bale_config.get_sandbox_network(cfg)
            sandbox = not args.no_sandbox
            if not sandbox:
                log(f"FORCE: --no-sandbox — the checkpoint dry-run "
                    f"executes UNCONFINED for this invocation "
                    f"(ADR-0016 escape; per-invocation only)",
                    force=True)
            log_path = (repo / ".bale" / "logs" /
                        f"open-{bundle_path.stem}.log")
            exit_code = dry_run_checkpoint(
                repo, members[checkpoint["path"]], checkpoint["path"],
                log_path=log_path, verbose=args.verbose,
                sandbox=sandbox, network=network)
            if exit_code == _CHECKPOINT_HOLD:
                log(f"expected-HOLD proof: the checkpoint FAILs against "
                    f"the unmodified live base (exit 1) — the oracle "
                    f"grades work that has not landed yet, exactly as a "
                    f"blind checkpoint should pre-session (dry-run log: "
                    f"{log_path})")
            elif exit_code == _CHECKPOINT_PASS:
                log(f"WARNING: the checkpoint PASSes against the "
                    f"unmodified live base (exit 0) — a vacuous oracle "
                    f"pre-work: it cannot distinguish the session's "
                    f"work landed from not landed. Proceeding (only "
                    f"exit 2 refuses, per the ratified row); the "
                    f"planner should confirm this checkpoint is "
                    f"invariant-only by intent.", force=True)
            else:
                fail(f"the checkpoint dry-run exited {exit_code} — "
                     f"outside the probe contract's 0/1 verdicts "
                     f"(TARBALL.md \u00a77.5), the oracle itself is "
                     f"defective, and a defective oracle refuses the "
                     f"whole open before any session exists (row 49's "
                     f"dry-run leg). Fix the checkpoint at the desk and "
                     f"re-emit the bundle; dry-run log: {log_path}")
        else:
            log("no checkpoint member: skipping the dry-run leg "
                "(nothing to prove)")

        pack_argv = compose_pack_argv(manifest, extracted)
        log(f"replaying pack invocation: "
            f"bale {shlex.join(pack_argv)}")
        parser = build_parser()
        pack_args = parser.parse_args(pack_argv)
        # The in-process pre-answered-intents channel (BALE.md §6.7):
        # the raw manifest array rides the namespace attribute cmd_pack
        # parses at its reject-early site; no CLI flag can spell this.
        pack_args.pre_answered = manifest["pre_answered"]
        return pack_args.func(pack_args)
    finally:
        shutil.rmtree(extract_dir, ignore_errors=True)
