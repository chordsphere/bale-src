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
3. **Gate the replay argv before the oracle runs** (boards 68, 122):
   the composed pack argv is parsed by the real CLI parser and every
   argv-only pack gate runs through bale_pack.run_pack_argv_gates —
   the flag pairs, the brief and checkpoint reads, the pre-exchange
   pass with its include-naming checkpoint gate, the supersession
   guards, forecast existence and disjointness — the same
   implementations cmd_pack runs, so a bundle the replay would refuse
   on its argv alone refuses here with that gate's own text and no
   dry-run is spent. Every refusal from here on names the
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

Two rehearsals stop part-way along this pipeline and write nothing (v0.4.45,
board row 122): `--check` stops after step 3, `--dry-run` after step 4 (its
dry-run log kept in a temp directory outside the repository), each printing
the rehearsal report bale_pack renders. On a second-desk bundle a rehearsal
predicts the desk, or its refusal, and records nothing.

`--json` (v0.4.48) changes none of this; it reports it. Under the flag the
whole run keeps json mode's stream discipline and each path that exits 0
ends on one line of JSON — outcome "opened", "second-desk" or "rehearsed",
rendered by bale_report.format_open_json, whose docstring owns the keys.
The replayed pack's own report line reaches cmd_open through the
`json_report_sink` namespace attribute (the third in-process channel, beside
`pre_answered` and `open_bundle`) and is folded into that one line.
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


def open_json_bundle_facts(bundle_path: Path, identity: dict) -> dict:
    """The `bundle` and `members` objects every `bale open --json` line
    carries (v0.4.48; format_open_json's docstring owns their meaning):

      bundle   {path: the absolute resolved path, sha256: of the file's
               bytes as read now, stem: bundle_identity's stem}
      members  {brief, checkpoint}: the manifest's published sha256 per
               slot — the hashes read_bundle verified, as bundle_identity
               carries them — or null

    Called after read_bundle accepted the file, so the re-read cannot
    fail short of the file changing underneath; if it does, the line
    still prints (the open itself is not refused over a report field)
    with sha256 "unreadable" and a FORCE-logged reason — never silent,
    bundle_identity's own fallback posture.
    """
    from __main__ import log  # lazy — see module docstring
    try:
        file_sha256 = hashlib.sha256(bundle_path.read_bytes()).hexdigest()
    except OSError as e:
        log(f"bale open --json: could not re-read {bundle_path} to hash it "
            f"({e}); the line's bundle.sha256 reads 'unreadable'",
            force=True)
        file_sha256 = "unreadable"
    return {
        "bundle": {
            "path": str(bundle_path.resolve()),
            "sha256": file_sha256,
            "stem": identity.get("stem"),
        },
        "members": {
            "brief": identity.get("brief_sha256"),
            "checkpoint": identity.get("checkpoint_sha256"),
        },
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
    49a-ii; gate order per boards 68 and 122). `--check` and `--dry-run`
    (v0.4.45, board row 122) rehearse a prefix of the same pipeline and
    stop, writing nothing.

    The pipeline, in trust order and cheapest-first; every refusal
    happens before any session state exists:

    1. resolve the bundle argument (apply's search-path semantics,
       kind "bundle"); refuse a file outside the reserved suffix —
       the suffix IS the recognizer (BALE.md §6.7);
    2. read_bundle(): gate the manifest, seal-check the archive,
       verify both member hashes; then recognize a second desk
       (row 123) — a rehearsal predicts that path instead of taking it
       (_rehearse_second_desk);
    3. when the checkpoint member ships, refuse up front if the project
       pins no [validation] base (naming the project root and the config
       files judged) — the bundle-level check, ahead of the argv gates
       so its wording, not the replayed --checkpoint-file's, is the one
       an operator sees;
    4. compose the replay argv, parse it through the real CLI parser (an
       unparseable stored argv refuses here), set the bundle's
       `pre_answered` intents on the namespace, and run every argv-only
       pack gate via bale_pack.run_pack_argv_gates — the same
       implementations cmd_pack runs, extended in v0.4.45 by the
       pre-exchange pass, so the include-naming checkpoint gate refuses
       here with no oracle spent. `--check` stops here and reports;
    5. when the checkpoint member ships, dry-run it read-only against the
       live base and judge the exit code — 1 is the expected-HOLD proof,
       0 proceeds with a loud vacuous-oracle warning, anything else
       refuses as a defective oracle. `--dry-run` stops here and
       reports, its dry-run log kept in a temp directory OUTSIDE the
       repository (a real open keeps it under .bale/logs/);
    6. echo and replay the composed pack invocation with the intents on
       the namespace (the in-process channel; BALE.md §6.7), returning
       cmd_pack's own exit code. The replay re-runs every gate at its
       own site — the early gates are a cost ordering, not a substitute.

    `--json` (v0.4.48) reports what the pipeline did as one line of JSON
    on stdout — format_open_json (bin/bale_report.py) owns the keys —
    without changing what it does: json mode's stream discipline engages
    before the first line can print, so every `[bale] ` line, the echoed
    verdicts, the rehearsal report, the second-desk summary and the
    opener's scissor block land on stderr; each path that exits 0 emits
    the one line last; the replayed pack hands its own report line to
    the `json_report_sink` channel instead of printing it, and the open
    folds it in. Refusals stay fail()-shaped, nothing on stdout.
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
        format_rehearsal_report,
        is_bundle_file,
        rehearse_supersession,
        run_pack_argv_gates,
    )
    from bale_report import (  # lazy — sibling
        OPEN_OUTCOME_OPENED,
        OPEN_OUTCOME_REHEARSED,
        OPEN_OUTCOME_SECOND_DESK,
        emit_json_line,
        enable_json_mode,
        format_open_json,
    )

    want_json = bool(getattr(args, "json", False))
    if want_json:
        # Stream discipline first, before any line can print (the module
        # docstring of bale_report states the contract).
        enable_json_mode()

    rehearsal = ("check" if getattr(args, "check", False)
                 else "dry-run" if getattr(args, "dry_run", False)
                 else None)
    verb = f"bale open --{rehearsal}" if rehearsal else "bale open"

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

    if rehearsal:
        log(f"{verb}: rehearsing planner bundle {bundle_path} against the "
            f"live tree — nothing will be written")
        if rehearsal == "check" and (args.no_sandbox or args.verbose):
            log("--check runs no checkpoint, so --no-sandbox/--verbose "
                "have nothing to act on here (use --dry-run to run it)")
    else:
        log(f"opening planner bundle {bundle_path}")
    manifest, members = read_bundle(bundle_path)

    # Row 123 (v0.4.44): a second open of a bundle whose session is still
    # open records another desk on that session instead of minting a new
    # sid. Recognized here — after the bundle verified, before the
    # pre-flight (whose disjointness gate would refuse a scoped bundle
    # against its own session) and long before the replay's read-only
    # sweep (which would close desk one's session under a piped stdin).
    identity = bundle_identity(bundle_path, manifest)
    # The bundle facts every --json line carries (format_open_json's
    # `bundle` and `members`); computed only under --json, so human mode
    # reads nothing it did not read before.
    json_facts = (open_json_bundle_facts(bundle_path, identity)
                  if want_json else None)

    def emit_open_line(outcome: str, **keys) -> None:
        if json_facts is not None:
            emit_json_line(format_open_json(
                outcome=outcome, bundle=json_facts["bundle"],
                members=json_facts["members"], **keys))

    match = find_open_session_for_bundle(repo, identity)
    if match is not None:
        if rehearsal:
            code = _rehearse_second_desk(verb, repo, match[0], match[1])
            if code == 0:
                emit_open_line(OPEN_OUTCOME_REHEARSED, rehearsal=rehearsal)
            return code
        desk_facts: dict = {}
        code = open_second_desk(repo, match[0], match[1], identity,
                                bundle_path, facts=desk_facts)
        if code == 0:
            emit_open_line(OPEN_OUTCOME_SECOND_DESK,
                           sid=match[0],
                           opener=desk_facts.get("opener"),
                           desk=desk_facts.get("desk"))
        return code

    brief = manifest["members"]["brief"]
    checkpoint = manifest["members"]["checkpoint"]
    for slot, entry in (("brief", brief), ("checkpoint", checkpoint)):
        if entry is None:
            log(f"member {slot}: explicit null (not shipped)")
        else:
            log(f"member {slot} verified: {entry['path']} "
                f"(sha256 {entry['sha256'][:12]}\u2026, LF-normalized)")

    if checkpoint is not None and bale_config.get_validation_base(cfg) is None:
        fail(f"the bundle ships a checkpoint member "
             f"({checkpoint['path']}) but this project pins no "
             f"[validation] base in bale.toml — the replayed "
             f"pack's --checkpoint-file would refuse for the "
             f"same reason. Configure [validation] base (see "
             f"`bale config init`), or use a bundle authored "
             f"for an oracle-less project."
             + config_judgment_suffix(repo))

    # Extract verified members to a tempdir that outlives the replayed
    # pack — cmd_pack reads the delivery-flag files during its own run.
    # Outside the repository, so a rehearsal writes nothing there.
    extract_dir = Path(tempfile.mkdtemp(prefix="bale-open-members-"))
    try:
        extracted: dict[str, Path] = {}
        for name, data in members.items():
            target = extract_dir / name
            target.write_bytes(data)
            extracted[name] = target

        # Boards 68 and 122: every argv-only pack gate runs here, BEFORE
        # the checkpoint leg. The replay argv is composed and parsed once
        # (build_parser is the real CLI parser, so a stored argv that
        # cannot parse refuses now — argparse's own usage error — with no
        # dry-run spent); the intents ride the namespace from here on, so
        # the gates parse them and the supersession prediction reads
        # them. The parsed namespace is the same object the replay below
        # executes.
        pack_argv = compose_pack_argv(manifest, extracted)
        parser = build_parser()
        pack_args = parser.parse_args(pack_argv)
        # The in-process pre-answered-intents channel (BALE.md §6.7):
        # the raw manifest array rides the namespace attribute cmd_pack
        # parses at its reject-early site; no CLI flag can spell this.
        pack_args.pre_answered = manifest["pre_answered"]
        facts = run_pack_argv_gates(repo, pack_args, cwd,
                                    announce=bool(rehearsal))
        supersession_row = (rehearse_supersession(facts) if rehearsal
                            else None)
        if rehearsal == "check":
            print(format_rehearsal_report(
                verb, repo, pack_args, facts,
                supersession_row=supersession_row,
                extra_rows=[("checkpoint dry-run",
                             "not run (--check spends no oracle)"
                             if checkpoint is not None
                             else "no checkpoint member")],
                trailer=[f"Rehearsal only: `bale open --dry-run` adds the "
                         f"checkpoint dry-run; `bale open` opens."]))
            emit_open_line(OPEN_OUTCOME_REHEARSED, rehearsal=rehearsal)
            return 0

        checkpoint_row = "no checkpoint member (nothing to dry-run)"
        # format_open_json's `checkpoint_dry_run` (v0.4.48): null unless
        # the dry-run below runs and is judged a verdict (exit 0 or 1).
        dry_run_report: Optional[dict] = None
        if checkpoint is not None:
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
            # A rehearsal keeps its dry-run log — and the sandbox
            # self-probe scratch that lives beside it — in a temp
            # directory outside the repository, kept for inspection and
            # named in the report: nothing lands under .bale/.
            if rehearsal:
                log_path = (Path(tempfile.mkdtemp(
                    prefix="bale-open-rehearsal-"))
                    / f"open-{bundle_path.stem}.log")
            else:
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
                checkpoint_row = (f"exit 1 — the expected HOLD (log: "
                                  f"{log_path})")
            elif exit_code == _CHECKPOINT_PASS:
                log(f"WARNING: the checkpoint PASSes against the "
                    f"unmodified live base (exit 0) — a vacuous oracle "
                    f"pre-work: it cannot distinguish the session's "
                    f"work landed from not landed. "
                    + ("A real open proceeds"
                       if rehearsal else "Proceeding")
                    + f" (only exit 2 refuses, per the ratified row); the "
                    f"planner should confirm this checkpoint is "
                    f"invariant-only by intent.", force=True)
                checkpoint_row = (f"exit 0 — PASSes pre-work (vacuous; "
                                  f"see the warning) (log: {log_path})")
            else:
                fail(f"the checkpoint dry-run exited {exit_code} — "
                     f"outside the probe contract's 0/1 verdicts "
                     f"(TARBALL.md \u00a77.5), the oracle itself is "
                     f"defective, and a defective oracle refuses the "
                     f"whole open before any session exists (row 49's "
                     f"dry-run leg). Fix the checkpoint at the desk and "
                     f"re-emit the bundle; dry-run log: {log_path}")
            dry_run_report = {"exit_code": exit_code, "log": str(log_path)}
        else:
            log("no checkpoint member: skipping the dry-run leg "
                "(nothing to prove)")

        if rehearsal == "dry-run":
            print(format_rehearsal_report(
                verb, repo, pack_args, facts,
                supersession_row=supersession_row,
                extra_rows=[("checkpoint dry-run", checkpoint_row)],
                trailer=["Rehearsal only: `bale open` with the same "
                         "bundle opens the session."]))
            emit_open_line(OPEN_OUTCOME_REHEARSED, rehearsal=rehearsal,
                           checkpoint_dry_run=dry_run_report)
            return 0

        log(f"replaying pack invocation: "
            f"bale {shlex.join(pack_argv)}")
        # The bundle channel (v0.4.41): the same in-process posture —
        # cmd_pack hands it to the open-time persist, which stamps it on
        # the opened attempt as `bundle`. No flag can spell it.
        pack_args.open_bundle = identity
        if json_facts is None:
            return pack_args.func(pack_args)
        # --json (v0.4.48): the replayed pack renders its report line into
        # the in-process sink instead of onto stdout (cmd_pack's
        # json_report_sink channel — no flag spells it), so the open's
        # line is the only stdout line and carries the pack's keys
        # verbatim. A pack that does not return 0 (fail() raises; the
        # interactive threshold abort returns 1) prints no line here,
        # the refusal shape.
        sink: list = []
        pack_args.json_report_sink = sink
        code = pack_args.func(pack_args)
        if code != 0:
            return code
        if len(sink) != 1:
            fail(f"bale open --json: the replayed pack exited 0 but handed "
                 f"back {len(sink)} report line(s), not one — an internal "
                 f"fault; the session it packed is as its own log records "
                 f"(nothing further was written by the open)")
        emit_open_line(OPEN_OUTCOME_OPENED, pack_report=json.loads(sink[0]),
                       checkpoint_dry_run=dry_run_report)
        return 0
    finally:
        shutil.rmtree(extract_dir, ignore_errors=True)


def _rehearse_second_desk(verb: str, repo: Path, sid: str,
                          record: dict) -> int:
    """A rehearsal's second-desk path (row 123 × row 122): predict what
    `bale open` would do with a bundle whose session is still open —
    record the next desk on that session, or refuse — and write nothing.
    As on the real path, no gate, dry-run, sweep or replay runs: a real
    second desk runs none, so there is nothing further to rehearse."""
    from __main__ import fail, log  # lazy — see module docstring
    from bale_pack import desk_qualified_name  # lazy — sibling
    from bale_report import format_summary_block  # lazy — sibling

    refusal = second_desk_refusal(sid, record)
    if refusal is not None:
        fail(refusal)
    desk = next_desk_name(record)
    log(f"second desk: this bundle opened session {sid}, which is still "
        f"open; `bale open` would record {desk} on it (no pre-flight, "
        f"dry-run, sweep, or replay runs on that path)")
    print(format_summary_block([
        ("rehearsal", verb),
        ("project root", str(repo.resolve())),
        ("second desk", f"would record {desk} on open session {sid} "
                        f"({desk_qualified_name(sid, desk)})"),
        ("not run", "the desk's opened attempt, its sweep commit, and the "
                    "opener — a second desk runs no gates or dry-run"),
        ("wrote", "nothing"),
    ], trailer=["Rehearsal only: `bale open` with the same bundle joins "
                "the session as that desk."]))
    return 0


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


def second_desk_refusal(sid: str, record: dict) -> Optional[str]:
    """The refusal a further desk on `sid` meets, or None when the record
    holds nothing but opens. Pure: open_second_desk raises it and the
    rehearsal verbs (v0.4.45, board row 122) predict it without writing.

    An 'opened' attempt after an apply-side event (an apply attempt, a
    HOLD, a refusal) would contradict the record, whose 'opened' means no
    close or apply event has landed yet.
    """
    later = [a.get("outcome") for a in (record.get("attempts") or [])
             if a.get("outcome") != "opened"]
    if not later:
        return None
    return (f"this bundle opened session {sid}, which is still open but "
            f"has recorded events past its opens (latest: {later[-1]}); "
            f"a further desk is recorded only while the session holds "
            f"nothing but opens, because an 'opened' attempt after an "
            f"apply-side event would contradict the record. Continue "
            f"that session where it stands (`bale status`), or close it "
            f"and re-open the bundle for a fresh session.")


def next_desk_name(record: dict) -> str:
    """The desk name the next open of the record's bundle would record."""
    return desk_name(sum(1 for a in (record.get("attempts") or [])
                         if a.get("outcome") == "opened") + 1)


def open_second_desk(repo: Path, sid: str, record: dict, identity: dict,
                     bundle_path: Path, *,
                     facts: Optional[dict] = None) -> int:
    """Record a further desk on open session `sid` and re-emit its opener.

    Writes one `opened` attempt (command 'open', the bundle identity,
    the session's recorded forecast, the open-time provenance stamp
    re-read from the session's stamped manifest, and `desk`) onto the
    existing record, journals the event into the session's own log, and
    prints the summary block ending in the session opener with the
    desk-qualified name, then copies that opener to the clipboard when
    a clipboard command is configured. Nothing else changes: one
    session stays open, no sid is minted, no sweep or replay runs, and
    the request tarball in the outbox is the one desk one opened with.
    Exit 0.

    Refuses (fail) — rather than silently minting a second session —
    when the record shows an event past its opens (an apply attempt, a
    HOLD, a refusal): the schema's 'opened' means no close or apply event
    has landed yet, so a desk appended after one would contradict the
    record; and when the session's stamped manifest is unreadable, since
    the opener cannot be rebuilt without it.

    `facts` (v0.4.48, `bale open --json`): when a dict is passed, the
    desk's report facts are written into it — `desk` (the name
    recorded) and `opener` (the desk opener's paste text,
    opener_paste_text of the block printed) — for cmd_open to render;
    nothing printed changes.
    """
    from __main__ import (  # lazy — see module docstring
        fail,
        log,
        read_session_scope,
        set_log_file,
        sweep_commit,
    )
    from bale_pack import (  # lazy — sibling
        desk_qualified_name,
        opener_paste_text,
        session_opener_block,
    )
    from bale_report import (  # lazy — sibling
        PASTE_BLOCK_OPENER,
        build_telemetry_attempt,
        copy_paste_block,
        format_summary_block,
        telemetry_home_display,
        write_telemetry_record,
    )

    refusal = second_desk_refusal(sid, record)
    if refusal is not None:
        fail(refusal)
    desk = next_desk_name(record)

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
    opener = session_opener_block(
        sid, goal, read_only=read_only, packed_at=packed_at,
        has_readme=stamped.get("readme") is not None, desk=desk)
    trailer += opener
    print(format_summary_block(rows, trailer=trailer))
    # Session clipboard-paste-blocks: this desk's opener (its own copy,
    # with the desk paragraph) goes to the clipboard like pack's does —
    # one stderr notice, exit unchanged (copy_paste_block's contract).
    paste_text = opener_paste_text(opener)
    copy_paste_block(repo, PASTE_BLOCK_OPENER, paste_text)
    if facts is not None:
        facts.update({"desk": desk, "opener": paste_text})
    return 0
