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
3. **Gate the replay argv before the oracle runs** (board 68): the
   composed pack argv is parsed by the real CLI parser and the
   arg-inspectable pack gates — forecast existence, forecast
   disjointness — run through bale_pack.pack_argv_preflight, the
   same implementations cmd_pack runs, so a bundle the replay would
   refuse on its argv alone refuses here with that gate's own text
   and no dry-run is spent. Every refusal from here on names the
   resolved project root and the config files judged.
4. **Dry-run the checkpoint read-only against the live base** (board
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
5. **Replay the pack argv** with the delivery flags supplied: the stored
   `pack_argv` never carries `--readme-file`/`--checkpoint-file`
   (validate_bundle_manifest refuses a stored one); this module
   appends them pointing at the extracted members — `--no-readme`
   when the brief slot is an explicit null — so member presence is
   the single source for the flags. The bundle's `pre_answered`
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
  3. Checkpoint dry-run               (~line 255)
  4. Argv replay + cmd_open           (~line 440)
  5. Second desk (row 123)            (after cmd_open)

A step 1.5 sits between steps 2 and 3 since v0.4.44 (board row 123):
**recognize a second desk.** When the verified bundle's identity matches
the `bundle` stamp on an `opened` attempt of a session that is still
open, the open records a further desk on THAT session — a second
`opened` attempt carrying `desk`, command `open` — re-emits its opener
with the desk-qualified name, and exits 0. No pre-flight, dry-run,
sweep, or replay runs on that path, so desk two can never close desk
one's session or mint a second sid. A bundle whose session has closed
opens a new session exactly as before.
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
    a Windows checkout) still verifies. Scoped to bundle reads: board
    50 (v0.4.15) applied the same one-line rule at the
    --checkpoint-file ingest via its own mirror
    (bale_pack.normalize_crlf) rather than a call into this module,
    and nothing outside this module calls this function for
    non-bundle bytes.
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


def bundle_identity(bundle_path: Path, manifest: dict) -> dict:
    """The bundle's identity for the opened attempt's `bundle` stamp
    (v0.4.41, close 16's Proposal 1; telemetry-record.schema.json
    attempts[].bundle): `{stem, brief_sha256, checkpoint_sha256,
    manifest_sha256}`.

    Called after read_bundle() has gated and verified the bundle, so
    the two member hashes are the manifest's PUBLISHED values — the
    ones read_bundle just checked every member's LF-normalized bytes
    against (null for a slot the bundle declares absent). The stem is
    the file name with BUNDLE_SUFFIX removed. manifest_sha256 hashes
    bundle.json's LF-normalized bytes, re-read here because read_bundle
    returns the parsed manifest, not its bytes: it pins the exact
    revision when two bundles share a brief but differ in argv or
    intents. The re-read cannot fail on a bundle read_bundle accepted
    moments ago short of the file changing underneath; if it does, the
    open is not worth refusing over a telemetry stamp, so the field
    reads "unreadable" and the log says why (never silent).
    """
    from __main__ import log  # lazy — see module docstring
    from bale_pack import BUNDLE_SUFFIX  # lazy — sibling
    name = bundle_path.name
    stem = name[:-len(BUNDLE_SUFFIX)] if name.endswith(BUNDLE_SUFFIX) \
        else bundle_path.stem
    members = manifest.get("members") or {}

    def published(slot: str) -> Optional[str]:
        entry = members.get(slot)
        return entry.get("sha256") if isinstance(entry, dict) else None

    manifest_sha256 = "unreadable"
    try:
        with tarfile.open(bundle_path, mode="r:gz") as tf:
            raw = tf.extractfile(tf.getmember(BUNDLE_MANIFEST_NAME))
            if raw is not None:
                manifest_sha256 = hashlib.sha256(
                    normalize_bundle_member(raw.read())).hexdigest()
    except (tarfile.TarError, OSError, KeyError) as e:
        log(f"bundle identity: could not re-read {BUNDLE_MANIFEST_NAME} "
            f"from {bundle_path} ({e}); the opened attempt's "
            f"bundle.manifest_sha256 reads 'unreadable'", force=True)
    return {
        "stem": stem or name,
        "brief_sha256": published("brief"),
        "checkpoint_sha256": published("checkpoint"),
        "manifest_sha256": manifest_sha256,
    }


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
               if sandbox else ", UNCONFINED — source in the FORCE: line above")
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
                      f"(ADR-0016) and bale.toml [sandbox] enabled = "
                      f"false the per-project one (v0.4.26)")

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
    """Return the full `pack` argv: the stored vector plus the supplied
    delivery flags.

    The stored `pack_argv` is the argument vector AFTER the `pack`
    subcommand and never carries a delivery flag
    (validate_bundle_manifest refused a stored one before this runs);
    the flags follow member presence — the single source, so the
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
    """`bale open <bundle>` — verify, gate, dry-run, replay (board
    49a-ii; gate order per board 68).

    The pipeline, in trust order and cheapest-first; every refusal
    happens before any session state exists:

    1. resolve the bundle argument (apply's search-path semantics,
       kind "bundle"); refuse a file outside the reserved suffix —
       the suffix IS the recognizer (BALE.md §6.7);
    2. read_bundle(): gate the manifest, seal-check the archive,
       verify both member hashes;
    3. compose the replay argv and parse it through the real CLI
       parser (an unparseable stored argv refuses here, before any
       oracle runs), then run the arg-inspectable pack gates —
       forecast existence and forecast disjointness — via
       bale_pack.pack_argv_preflight (board 68): cheap gates before
       the expensive oracle execution, each the one implementation
       cmd_pack itself runs, so a bundle the replay would refuse on
       its argv alone refuses with that gate's own text and no
       dry-run runs;
    4. when the checkpoint member ships: refuse up front if the
       project pins no [validation] base (the same refusal
       `--checkpoint-file` would give, moved before the dry-run's
       cost, naming the project root and the config files judged),
       then dry-run it read-only against the live base and
       judge the exit code — 1 is the expected-HOLD proof, 0
       proceeds with a loud vacuous-oracle warning, anything else
       refuses the open as a defective oracle;
    5. echo and replay the composed pack invocation with the bundle's
       `pre_answered` intents on the namespace (the in-process
       channel; BALE.md §6.7), returning cmd_pack's own exit code.
       The replay re-runs every gate at its own site — the pre-flight
       is a cost ordering, not a substitute; the checkpoint-blindness
       gate in particular runs only there.
    """
    from __main__ import (  # lazy — see module docstring
        build_parser,
        fail,
        log,
        repo_root,
        resolve_inbound_path,
    )
    import bale_config  # lazy — sibling module
    from bale_pack import (  # lazy — sibling
        BUNDLE_SUFFIX,
        config_judgment_suffix,
        is_bundle_file,
        pack_argv_preflight,
    )

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

    # Row 123 (v0.4.44): a second open of a bundle whose session is still
    # open records another desk on that session instead of minting a new
    # sid. Recognized here — after the bundle verified, before the
    # pre-flight (whose disjointness gate would refuse a scoped bundle
    # against its own session) and long before the replay's read-only
    # sweep (which would close desk one's session under a piped stdin).
    identity = bundle_identity(bundle_path, manifest)
    match = find_open_session_for_bundle(repo, identity)
    if match is not None:
        return open_second_desk(repo, match[0], match[1], identity,
                                bundle_path)

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

        # Board 68: the arg-inspectable pack gates run here, BEFORE the
        # checkpoint leg. The replay argv is composed and parsed once
        # (build_parser is the real CLI parser, so a stored argv that
        # cannot parse refuses now — argparse's own usage error — with
        # no dry-run spent), then pack_argv_preflight evaluates the
        # forecast-existence and forecast-disjointness gates with the
        # implementations cmd_pack itself runs. The parsed namespace is
        # the same object the replay below executes.
        pack_argv = compose_pack_argv(manifest, extracted)
        parser = build_parser()
        pack_args = parser.parse_args(pack_argv)
        pack_argv_preflight(repo, pack_args)

        if checkpoint is not None:
            if bale_config.get_validation_base(cfg) is None:
                fail(f"the bundle ships a checkpoint member "
                     f"({checkpoint['path']}) but this project pins no "
                     f"[validation] base in bale.toml — the replayed "
                     f"pack's --checkpoint-file would refuse for the "
                     f"same reason. Configure [validation] base (see "
                     f"`bale config init`), or use a bundle authored "
                     f"for an oracle-less project."
                     + config_judgment_suffix(repo))
            network = bale_config.get_sandbox_network(cfg)
            # Sandbox-off by config (v0.4.26, board 75) honors the same
            # project-layer key apply does: a namespace-less host runs
            # `bale open` too, and the dry-run is the one other confined
            # leg. Same loudness contract — each escape FORCE-logs
            # naming itself, both when both are present; silence is
            # the one forbidden outcome. log(force=True) supplies the
            # `FORCE: ` prefix itself (board 68 rider: the message
            # text carries none, or the line reads FORCE: FORCE:).
            sandbox_enabled = bale_config.get_sandbox_enabled(cfg)
            sandbox = sandbox_enabled and not args.no_sandbox
            if args.no_sandbox:
                log(f"--no-sandbox — the checkpoint dry-run "
                    f"executes UNCONFINED for this invocation "
                    f"(ADR-0016 escape; per-invocation only)"
                    + (" (redundant beside bale.toml [sandbox] enabled "
                       "= false)" if not sandbox_enabled else ""),
                    force=True)
            if not sandbox_enabled:
                log(f"bale.toml [sandbox] enabled = false "
                    f"(project layer) — the checkpoint dry-run executes "
                    f"UNCONFINED: operator privileges, inherited "
                    f"environment, network on",
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

        log(f"replaying pack invocation: "
            f"bale {shlex.join(pack_argv)}")
        # The in-process pre-answered-intents channel (BALE.md §6.7):
        # the raw manifest array rides the namespace attribute cmd_pack
        # parses at its reject-early site; no CLI flag can spell this.
        # pack_args was parsed above, ahead of the dry-run (board 68).
        pack_args.pre_answered = manifest["pre_answered"]
        # The bundle channel (v0.4.41): the same in-process posture —
        # cmd_pack hands it to the open-time persist, which stamps it on
        # the opened attempt as `bundle`. No flag can spell it.
        pack_args.open_bundle = identity
        return pack_args.func(pack_args)
    finally:
        shutil.rmtree(extract_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# 5. Second desk (v0.4.44, board row 123)
# ---------------------------------------------------------------------------
#
# The specimen: one read-only planner session run at two desks under one
# sid, whose record carried a single `opened` attempt — the two-desk
# experiment was invisible. Re-opening the bundle used to decline the
# sweep (piped stdin) and mint a second sid. Now the second open is
# recognized by bundle identity and recorded on the same record; it is a
# suffix, never a refusal (the paired-desk sitting's ruling: refusing
# would have blocked the experiment that produced the finding).

# The identity keys a second desk must match. The stem is deliberately
# NOT among them: a renamed copy of the same bundle (a browser's
# "name (1).bale-bundle") is the same bundle, and its stem still rides the
# desk attempt's `bundle` stamp for the record.
DESK_IDENTITY_KEYS = ("manifest_sha256", "brief_sha256", "checkpoint_sha256")


def desk_name(opened_count: int) -> str:
    """The desk value for the attempt that makes `opened_count` opens:
    'desk-N' (the first open carries no key and reads as desk-1)."""
    return f"desk-{opened_count}"


def bundle_identity_matches(recorded, identity: dict) -> bool:
    """True when a recorded `bundle` stamp names the same bundle revision
    as `identity`. An identity whose manifest hash could not be read
    ('unreadable', bundle_identity's loud fallback) never matches — a
    second desk is recognized only on a hash, never guessed."""
    if not isinstance(recorded, dict):
        return False
    if identity.get("manifest_sha256") in (None, "unreadable"):
        return False
    return all(recorded.get(k) == identity.get(k) for k in DESK_IDENTITY_KEYS)


def find_open_session_for_bundle(repo: Path,
                                 identity: dict) -> Optional[tuple]:
    """(sid, record) of the open session an earlier open of this bundle
    created, or None.

    Reads the registry's open sessions oldest-first and, for each, its
    telemetry record: a session matches when any `opened` attempt's
    `bundle` stamp matches `identity` (bundle_identity_matches). A closed
    session never matches — it is not in the registry — so a bundle whose
    session has closed opens a new session exactly as before. More than
    one match (two sessions opened from one bundle before v0.4.44) logs
    the others and returns the oldest, the one the first desk opened.
    """
    from __main__ import log, open_sessions  # lazy — see module docstring
    from bale_report import read_telemetry_record  # lazy — sibling
    matches = []
    for sid in open_sessions(repo):
        record = read_telemetry_record(repo, sid)
        if not record:
            continue
        if any(a.get("outcome") == "opened"
               and bundle_identity_matches(a.get("bundle"), identity)
               for a in record.get("attempts") or []):
            matches.append((sid, record))
    if not matches:
        return None
    if len(matches) > 1:
        log(f"second desk: {len(matches)} open sessions were opened from "
            f"this bundle ({', '.join(m[0] for m in matches)}); recording "
            f"the desk on the oldest, {matches[0][0]}")
    return matches[0]


def _record_is_tracked(repo: Path, rel: str) -> bool:
    """Whether git tracks `rel` — the desk append sweeps only a record the
    operator already committed (an untracked open-time record stays
    untracked until close, exactly as pack leaves it)."""
    r = subprocess.run(["git", "ls-files", "--error-unmatch", "--", rel],
                       cwd=str(repo), capture_output=True, text=True)
    return r.returncode == 0


def open_second_desk(repo: Path, sid: str, record: dict, identity: dict,
                     bundle_path: Path) -> int:
    """Record a further desk on open session `sid` and re-emit its opener.

    Writes one `opened` attempt (command 'open', the bundle identity,
    the session's recorded forecast, the open-time provenance stamp
    re-read from the session's stamped manifest, and `desk`) onto the
    existing record, journals the event into the session's own log, and
    prints the summary block ending in the session opener with the
    desk-qualified name. Nothing else changes: one session stays open,
    no sid is minted, no sweep or replay runs, and the request tarball in
    the outbox is the one desk one opened with. Exit 0.

    Refuses (fail) — rather than silently minting a second session —
    when the record shows an event past its opens (an apply attempt, a
    HOLD, a refusal): the schema's 'opened' means no close or apply event
    has landed yet, so a desk appended after one would contradict the
    record; and when the session's stamped manifest is unreadable, since
    the opener cannot be rebuilt without it.
    """
    from __main__ import (  # lazy — see module docstring
        fail,
        log,
        read_session_scope,
        set_log_file,
        sweep_commit,
    )
    from bale_pack import desk_qualified_name, session_opener_block  # lazy — sibling
    from bale_report import (  # lazy — sibling
        build_telemetry_attempt,
        format_summary_block,
        telemetry_home_display,
        write_telemetry_record,
    )

    attempts = record.get("attempts") or []
    later = [a.get("outcome") for a in attempts
             if a.get("outcome") != "opened"]
    if later:
        fail(f"this bundle opened session {sid}, which is still open but "
             f"has recorded events past its opens (latest: {later[-1]}); "
             f"a further desk is recorded only while the session holds "
             f"nothing but opens, because an 'opened' attempt after an "
             f"apply-side event would contradict the record. Continue "
             f"that session where it stands (`bale status`), or close it "
             f"and re-open the bundle for a fresh session.")
    desk = desk_name(sum(1 for a in attempts
                         if a.get("outcome") == "opened") + 1)

    manifest_path = repo / ".bale" / "sessions" / sid / "manifest.json"
    try:
        stamped = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        fail(f"second desk on {sid}: could not read the session's stamped "
             f"manifest at {manifest_path} ({e}); the opener cannot be "
             f"rebuilt without its goal and pack instant.")

    log_rel = f".bale/logs/{sid}.log"
    set_log_file(repo / log_rel)
    log(f"second desk: bundle {bundle_path.name} matches the bundle open "
        f"session {sid} was opened from; recording {desk} on that session "
        f"instead of opening a new one (no pre-flight, dry-run, sweep, or "
        f"replay runs on this path)")

    attempt = build_telemetry_attempt(
        outcome="opened", command="open",
        scope=read_session_scope(repo, sid), log_path=log_rel,
        bundle=identity)
    provenance = stamped.get("provenance")
    if isinstance(provenance, dict):
        stamp = {k: provenance[k] for k in
                 ("work_class", "packer", "packed_at")
                 if isinstance(provenance.get(k), str) and provenance[k]}
        if stamp:
            attempt["provenance"] = stamp
    attempt["desk"] = desk
    rel = write_telemetry_record(repo, sid, attempt)
    if rel:
        log(f"second desk: {desk} recorded as an 'opened' attempt "
            f"(command 'open') on {rel}")
        if _record_is_tracked(repo, rel):
            sweep_commit(repo, sid, f"opened {desk}", [rel])
        else:
            log(f"second desk: {rel} is untracked (the open-time record "
                f"stays untracked until the session closes); nothing to "
                f"sweep")
    # A write failure already logged force=True inside
    # write_telemetry_record; the desk is still worth its opener.

    goal = stamped.get("goal", "")
    read_only = stamped.get("resolved_scope") == []
    packed_at = (provenance or {}).get("packed_at", "unknown") \
        if isinstance(provenance, dict) else "unknown"
    tarball = repo / ".bale" / "outbox" / f"request-{sid}.tar.gz"
    rows = [
        ("session id", sid),
        ("desk", f"{desk} ({desk_qualified_name(sid, desk)})"),
        ("telemetry", rel if rel else
         f"write failed — see log (home: {telemetry_home_display(repo)})"),
        ("tarball", str(tarball) if tarball.is_file()
         else f"{tarball} (not in the outbox — use the copy desk one used)"),
    ]
    trailer = [
        f"Attach the same request tarball to the new chat; this desk "
        f"joins session {sid} and opens nothing new.",
    ]
    trailer += session_opener_block(
        sid, goal, read_only=read_only, packed_at=packed_at,
        has_readme=stamped.get("readme") is not None, desk=desk)
    print(format_summary_block(rows, trailer=trailer))
    return 0
