#!/usr/bin/env python3
"""craft_response.py — mechanical scaffolder for a bale response directory.

A WORKER runs this against its own response-NNN/ directory while
building a response, without bale installed. It mechanizes the
computed half of TARBALL.md §5.2/§5.2.1 and the §5.1.1 scaffold, and
scaffolds all three response kinds (`--kind`, default `normal`):

- (normal) walks `files/`, computes every `size_bytes` and `sha256`,
  and emits the `changes[]` skeleton in paste-ready form — mirror
  prefix stripped, computed values filled, `action` and `reason` left
  empty for the worker (reason is judgment; the tool never generates
  it);
- (normal) emits `deleted`-entry stubs on request (`--deleted PATH`);
  the two hand-written literals of the old §5.2.1 recipe —
  `size_bytes: 0`, `sha256: null` — are this tool's to write now;
- (normal) emits the manifest skeleton (`session_id` / `responds_to`
  from `--sid`, `response_kind: "normal"`, the empty structured
  fields present) and the `apply.sh` scaffold: the §5.1.1 no-op when
  nothing needs it, otherwise `rm -f` lines for deletions and
  per-path `chmod +x` lines for files the worker names with
  `--executable`;
- (bailout, §5.6) emits the manifest skeleton with the §5.6.2 empty
  change surfaces, and under `--write` the full artifact set: the
  no-op `apply.sh` and `validation.sh`, the `handoff.md` scaffold
  carrying §5.7's section headers and nothing else (handoff CONTENT
  is judgment and stays the worker's), and the `diagnostics.json`
  skeleton carrying the schema's required keys — `session_id` filled
  (mechanical), everything else empty;
- (clarification, §5.9) emits the manifest skeleton with the same
  empty change surfaces plus `questions[]` seeded with four-field
  entry stubs (`--questions N`, default 1), and under `--write` the
  no-op `apply.sh` and `validation.sh`;
- (normal) `--validation-epilogue` prints paste-ready `validation.sh`
  fragments: the §7.3 claims reconciliation epilogue (a
  verdict-recording helper the worker's checks feed, and the
  reconciliation pass that reads `staging/.bale-manifest.json` and
  prints the claims-vs-verdict block — diagnostic, never
  gatekeeping), plus one §7.7 exec-bit assertion per path named with
  `--executable` — generated from the same list that drives
  `apply.sh`'s chmod lines, so the two emissions cannot disagree
  within an invocation. WHICH checks run stays the worker's judgment
  (§7.2): the emission names no checks and suggests none; it
  mechanizes the reconciliation shape and the exec-bit assertion
  shape only, which is the ratified carve-out to the no-scaffold pin
  below — a fragment the worker pastes, never an emitted
  `validation.sh`;
- (normal) `--doc-assertions` prints paste-ready `validation.sh`
  blocks for the per-project doc-contract rows of `DOCS.md` §9 and
  `CODE.md` §10 — the rows those tables label `contract` with
  enforcement "response's validation.sh". Parameterized and opt-in
  (bale stays project-agnostic; nothing runs unconditionally):
  `--index PATH` emits INDEX coherence both directions, `--adr-dir
  PATH` emits the ADR guards (append-only, the two sanctioned flips
  proven by reverse transform against pre-change sha256s embedded
  from `--adr-baseline DIR`, sequential numbering), `--prune-reasons`
  emits the archive-vs-delete reason check, and `--index-header PATH`
  (repeatable) emits banner-vs-header coherence per named file. The
  enforcement recipes those tables used to carry in prose live in
  these emissions now, where they cannot drift from what runs;
- (probe, §4.2) `--probe SLUG` emits the canonical paste-back probe
  skeleton to stdout — the shape (shebang, three-line purpose header
  with the read-only declaration verbatim, the probe() wrapper, the
  PROBE BEGIN/END sentinels carrying the slug, and the
  capture-then-count integrity trailer) final; the what/why header
  lines and the one example labeled section (its cap-and-truncation
  pattern shown) are loud TODO placeholders, in comments and strings
  only so the emission stays valid bash. A probe is chat-ephemeral
  (§4.2): no response directory is read, required, or accepted, and
  no lint runs on it — the architect audits the pasted block by eye,
  so the unfilled placeholders are the unfilled-cannot-pass analog:
  visibly not ready to paste. The scaffold's tail is the opt-in
  clipboard epilogue (registry fold-in, ratified 2026-08-18,
  configurable-never-core): when a `clipboard_command` under
  `[probe]` is readable from `bale.toml` (looked up in `./bale.toml`
  then `./context/bale.toml` — the repo-root and request-root
  layouts), the scaffold ends with a tee of the sentinel-bracketed
  block into that command, reporting success or failure loudly at
  runtime and never failing the probe over it; the sentinel banners
  always emit either way (the dependency-free selection aid), and
  the unset or misconfigured path emits remedy text walking the
  operator through setup instead — never fails, never silently
  skips. The key's future config-side carrier (bin/bale_config.py)
  must land the same spelling: `[probe] clipboard_command`;

- (bundle, board 49b; format home is the bale project's design doc,
  §6.7 there) `--bundle STEM` assembles a planner bundle — the
  desk-side emission half, so the authoring desk never hand-composes
  argv or hash blocks. It writes `<STEM>{BUNDLE_SUFFIX}` (a gzipped
  tar, members flat at the archive root: `bundle.json` plus exactly
  the declared members — `brief.md` from `--brief`, `checkpoint.sh`
  from `--checkpoint`) and prints the paste line the desk ships
  beside it — `bale open <filename>`, the bundle FILENAME only, so a
  downloads-dir save is paste-ready under the consumer's search-path
  resolution. Member bytes are LF-normalized at write (every CRLF
  becomes LF) and each published sha256 is the digest of those
  normalized bytes — the format's own rule, so a transport-mangled
  copy still verifies. The stored `pack_argv` never carries the
  delivery flags (`--readme-file` / `--checkpoint-file`) or the
  `pack` verb itself — the consumer injects delivery from member
  presence — and the tool refuses an argv that tries (argument
  hygiene, same posture as the rest of this surface). Pre-answered
  intents (`--pre-answered PROMPT=SUBJECT`, closed vocabulary:
  INTENT_PROMPTS below) ride `pre_answered`; `[]` is the honest
  empty. Emission is deterministic (fixed tar metadata, zeroed gzip
  mtime): identical inputs produce identical bytes, so a re-run onto
  an existing identical bundle is an idempotent no-op and only
  differing bytes need `--force`. The emitter assembles — it never
  executes the checkpoint or the pack; the dry-run proof and the
  authoritative manifest gate (validate_bundle_manifest) are the
  consuming verb's alone. A worker never authors, requests, or names
  a real bundle file (worker blindness — the bundle is
  oracle-bearing); this mode is the DESK's, and tests exercise it
  under temp dirs only.

- (exchange, §5.9.2) `--emit-block <file|->` renders the
  counterpart-facing paste block for a filled clarification manifest or
  a filled worker exchange record, to stdout. This is the WORKER side of
  the exchange thread: `bale relay` renders the same block for records
  it ingests, but relay runs in the planner's repo against a suspended
  session's `.bale/` state, which a worker session does not have. A
  manifest (`response_kind: "clarification"`) is normalized to its
  `from: worker` reading — `round` from `--round` (default 1),
  `created_at` stamped at emission, `session_id` and `questions[]`
  lifted from the manifest; a record carrying a `from` key is emitted
  as-is once it validates. A `from: planner` record refuses (that side
  is relay's, and it needs the thread to sequence against), and a
  `--round` contradicting a record's own round refuses rather than
  rewrites. The rendering is byte-identical to section 29's for the same
  record — the constants and layout are re-declared here, per the
  INTENT_PROMPTS precedent, and the parity suite is what keeps the two
  from drifting. stdout is the block and only the block, so
  `--emit-block r.json > block.txt` captures it clean;

For the normal kind, `validation.sh` remains un-emitted on purpose:
there it is the worker's hypothesis test (TARBALL.md §7) — judgment,
never scaffolded. The no-op validation.sh exists only for the two
kinds whose contract fixes it as a no-op.

THE CRAFTER NEVER VALIDATES ITS OWN OUTPUT. `tools/response_lint.py`
is the separately authored, separately maintained judge; this module
does not import from it, share code with it, or get imported by it.
The workflow is: craft, fill the judgment fields, then the lint
judges. An unfilled skeleton is deliberately lint-invalid (empty
`action`, `reason`, `summary`), so it cannot pass review by accident.

Usage:
    craft_response.py <response-dir> --sid SESSION_ID [options]
    craft_response.py --probe SLUG
    craft_response.py --bundle STEM --pack-arg TOKEN...
                      (--brief FILE | --no-brief) [--checkpoint FILE]
                      [--pre-answered PROMPT=SUBJECT]... [--out-dir DIR]
    craft_response.py --emit-block FILE [--round N]

Modes (mutually exclusive; default prints the manifest skeleton):
    (default)       print the manifest-skeleton JSON to stdout
    --changes-only  print only the changes[] array (normal kind only)
    --apply-only    print only the apply.sh scaffold
    --write         write the kind's artifact set into the response dir
                    (normal: manifest.json, apply.sh; clarification:
                    + validation.sh; bailout: + validation.sh,
                    handoff.md, diagnostics.json). Refuses to
                    overwrite; --force to allow.
    --validation-epilogue
                    print the paste-ready validation.sh fragments
                    (normal kind only): the reconciliation epilogue,
                    plus exec-bit assertions for --executable paths.
                    --fragment {definitions,assertions,call} emits one
                    separable part instead of the combined block, so
                    pasting the definitions can never fire the
                    reconcile_claims call early.
    --doc-assertions
                    print paste-ready validation.sh blocks for the
                    DOCS.md §9 / CODE.md §10 contract rows (normal
                    kind only); select blocks with --index, --adr-dir
                    (+ --adr-baseline), --prune-reasons,
                    --index-header.
    --probe SLUG    print the TARBALL.md §4.2 probe skeleton to stdout.
                    Takes no response dir and combines with none of the
                    response-directory flags — a probe is a chat
                    paste-back, not a response artifact.
    --bundle STEM   assemble the planner bundle STEM + the reserved
                    suffix and print the `bale open` paste line to
                    stdout. Desk-side only; takes no response dir and
                    combines with none of the response-directory flags
                    (or --probe).
    --emit-block FILE
                    render the exchange paste block for FILE (a filled
                    clarification manifest or a filled worker exchange
                    record; `-` reads stdin) to stdout, byte-identical
                    to `bale relay`'s. Takes no response dir and
                    combines with none of the response-directory flags
                    (or --probe / --bundle). --round N sets the round
                    on the manifest path and asserts it on the record
                    path.

Bundle options (only with --bundle):
    --pack-arg TOKEN    one pack-argv token, repeatable in order — the
                        argument vector AFTER the pack subcommand; at
                        least one required. Never a delivery flag and
                        never the verb itself (both refuse). A token
                        that itself starts with a dash uses the
                        =-glued spelling: --pack-arg=--slug
    --brief FILE        the brief member (stored as brief.md)
    --no-brief          deliberate no-brief bundle (members.brief null)
    --checkpoint FILE   the blind-checkpoint member (stored as
                        checkpoint.sh); absent = members.checkpoint null
    --pre-answered P=S  one pre-answered intent, prompt=subject,
                        repeatable; prompt from the closed vocabulary
    --out-dir DIR       where the bundle file lands (default: cwd)

Options:
    --kind KIND         normal (default) | bailout | clarification
    --questions N       clarification only: number of question-entry
                        stubs to seed (default 1)
    --deleted PATH      normal only: add a deleted-entry stub (repeatable)
    --executable PATH   normal only: add a chmod +x line for a files/
                        path (repeatable)
    --sid SESSION_ID    session id for session_id and responds_to;
                        required except under --changes-only/--apply-only

Exit codes:
    0  success
    2  the tool errored (bad usage, unreadable dir, incoherent flags)
    (1 is reserved; the crafter has no findings — findings are the
    lint's business.)

Stdlib only. Python 3.10+. No network. No bale imports. No
response_lint imports.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import sys
import tarfile
from pathlib import Path, PurePosixPath

EXIT_OK = 0
EXIT_ERROR = 2

KINDS = ("normal", "bailout", "clarification")

# --- Planner-bundle constants (board 49b, the emission half) ---
#
# Re-declared from bin/bale_pack.py (BUNDLE_SUFFIX, INTENT_PROMPTS)
# because this tool imports nothing from bale — it must run standalone
# wherever a request tarball lands. Two homes without a pin is how
# citations drift, so the duplication carries a drift guard: the bale
# install's validate.sh asserts equality against bale_pack's constants,
# and tests/test_craft_response.py pins the same parity unit-shaped.
# A session changing either home changes both in the same response.
BUNDLE_SUFFIX = ".bale-bundle"
INTENT_PROMPTS = ("supersede",)

# The two delivery flags the CONSUMER injects from member presence —
# never stored in pack_argv (the member's presence is the single
# source, so the stored argv can never disagree with the shipped
# bytes). The emitter refuses an argv naming one, bare or =-glued; the
# consumer-side validator (validate_bundle_manifest) independently
# refuses the same, so a hand-rolled bundle is caught there too.
DELIVERY_FLAGS = ("--readme-file", "--checkpoint-file")

# Fixed flat archive-member names (the schema's stated conventions).
# Internal to the container — the desk names the stem, never these.
BRIEF_MEMBER = "brief.md"
CHECKPOINT_MEMBER = "checkpoint.sh"

# The unfilled-brief sentinel `bale pack --readme-file` refuses on
# (TARBALL.md §3.4). The literal is duplicated from bin/bale_pack.py's
# guard (no named constant exists there); the parity test in
# tests/test_craft_response.py pins that the pack source still carries
# it. Refusing here fails the half-generated brief at the desk, where
# the fix is immediate, instead of at the operator's `bale open`.
BRIEF_PLACEHOLDER = "TODO(brief)"

# --- Probe clipboard epilogue (registry fold-in, ratified 2026-08-18,
#     configurable-never-core) ---
#
# The opt-in config key naming the environment's clipboard command.
# NAMED LOUDLY on purpose: the config-side carrier (the next
# bin/bale_config.py touch) must land the same spelling — section
# `[probe]`, key `clipboard_command`, a one-line TOML basic string
# whose value is the shell command probe output is piped into (e.g.
# "pbcopy", "xclip -selection clipboard"). This tool reads the key
# with a deliberately minimal single-key scan (stdlib-only, no TOML
# parser is available standalone on 3.10), looked up in ./bale.toml
# then ./context/bale.toml — the repo-root and request-root layouts.
CLIPBOARD_SECTION = "probe"
CLIPBOARD_KEY = "clipboard_command"
CLIPBOARD_CONFIG_CANDIDATES = ("bale.toml", "context/bale.toml")

APPLY_NOOP = """#!/usr/bin/env bash
# No additional operations for this session.
exit 0
"""

APPLY_HEADER = """#!/usr/bin/env bash
set -euo pipefail
"""

# TARBALL.md fixes validation.sh as a no-op on the two non-normal kinds
# (§5.6.1 for bailouts, §5.9.2 for clarifications): nothing changed, so
# there is nothing to test. On the normal kind validation.sh is the
# worker's hypothesis test (§7) and this tool never emits it.
VALIDATION_NOOP_BY_KIND = {
    "bailout": """#!/usr/bin/env bash
# No checks to run — a bailout response carries no change set
# (TARBALL.md 5.6.2).
exit 0
""",
    "clarification": """#!/usr/bin/env bash
# No checks to run — a clarification response carries no change set
# (TARBALL.md 5.9.2).
exit 0
""",
}

# TARBALL.md §5.7's required sections, in the required order, and
# nothing else: the scaffold is the section list; the content under
# each header is judgment and stays the worker's.
HANDOFF_SCAFFOLD = """# Handoff

## Original goal

## What I loaded

## What I explored

## What I learned

## Reading plan for the next session

## Salvageable work
"""

# The four-field questions[] entry stub of TARBALL.md §5.9.2 /
# response-manifest.schema.json. Every value is an empty string on
# purpose: an unfilled skeleton is deliberately lint-invalid.
QUESTION_STUB_KEYS = ("question", "context", "default_assumption",
                     "why_blocked")

# The TARBALL.md §4.2 canonical probe skeleton. Real and final: the
# shebang, the three-line purpose-header shape (its read-only line
# verbatim from §4.2), the probe() wrapper, the sentinels carrying the
# slug, and the capture-then-count integrity trailer. Loud TODO
# placeholders (comments and strings only, so `bash -n` stays clean):
# the what/why header lines and one example labeled section with the
# cap-and-truncation-marker pattern shown. Sections are judgment; the
# shape is not. No judge runs on a probe — it is a chat paste-back the
# architect audits by eye (§4.2), so unfilled placeholders are the
# unfilled-cannot-pass analog: visibly not ready to paste.
PROBE_SCAFFOLD = """\
#!/usr/bin/env bash
# PROBE {slug}: TODO(worker) — what this asks, in one line.
# Why: TODO(worker) — the gap this fills, in one line.
# Read-only: writes nothing anywhere; stdout is the only output.

probe() {{
  # TODO(worker): replace this placeholder with the real sections —
  # one labeled section per question, every command's output capped,
  # an explicit truncation marker when the cap bites (TARBALL.md 4.2).
  # The cap-and-truncation pattern, worked for one command:
  #   git status --porcelain=v1 2>&1 | head -n 40
  #   n=$(git status --porcelain=v1 2>/dev/null | wc -l)
  #   [ "$n" -gt 40 ] && echo "[truncated: $n lines total, showing 40]"
  echo "--- section: TODO-example ---"
  echo "TODO(worker): unfilled probe placeholder — not ready to paste"
}}

out="$(probe 2>&1)"
emit_probe_block() {{
  echo "=== PROBE BEGIN {slug} ==="
  printf '%s\\n' "$out"
  printf -- '--- integrity: %s lines ---\\n' "$(printf '%s\\n' "$out" | wc -l | tr -d ' ')"
  echo "=== PROBE END {slug} ==="
}}
emit_probe_block
"""

# The keyless tail of the probe scaffold: remedy text walking the
# operator through the clipboard opt-in (TARBALL.md 4.3). Comments
# only — nothing runs, nothing fails, and the manual selection path
# (the sentinel banners) is named. Emitted whenever no usable
# clipboard_command was readable at craft time.
PROBE_CLIPBOARD_REMEDY = """\
# Clipboard epilogue not emitted (opt-in, unset at craft time). To have
# this scaffold tee its own output to your clipboard, set in bale.toml:
#     [probe]
#     clipboard_command = "<your clipboard command>"   # e.g. pbcopy
# and ship bale.toml in the request's context/ so the crafter can read
# it (it looks in ./bale.toml, then ./context/bale.toml). Manual path:
# select between the PROBE BEGIN/END banners above and copy.
"""

# The key-set tail: tee the sentinel-bracketed block into the
# configured command. Loud either way at runtime, and the epilogue can
# never fail the probe — a missing or failing clipboard command reports
# and the banners remain the dependency-free selection aid.
PROBE_CLIPBOARD_EPILOGUE = """\
# Clipboard epilogue (opt-in; bale.toml [probe] clipboard_command).
# Tees the sentinel-bracketed block above into the configured command;
# the banners stay the dependency-free selection aid if this fails.
if emit_probe_block | {clip} 2>/dev/null; then
  echo "[clipboard] probe output copied (bale.toml [probe] clipboard_command)" >&2
else
  echo "[clipboard] the configured clipboard command failed or is missing — select between the PROBE BEGIN/END banners and copy manually" >&2
fi
"""


# The TARBALL.md §7.3 claims reconciliation epilogue. Real and final:
# the verdict-recording helper, and the reconciliation pass that reads
# the manifest bale places at staging/.bale-manifest.json and prints
# the claims-vs-verdict block. Semantics mirror §7.3 exactly: [agree]
# on a matching prediction, [DISAGREE] only on a pass/fail cross,
# [n/a] when the verdict is a skip (or missing) or the claim made no
# prediction (untested/unknown). Diagnostic, never gatekeeping: the
# epilogue neither sets nor reads exit_code (§7.3, §7.5). WHICH checks
# run is the worker's judgment (§7.2) — nothing here names or suggests
# a check; the shape alone is mechanized.
RECONCILE_EPILOGUE = """\
# --- claims reconciliation (crafted; TARBALL.md 7.3) ---
# Paste this block BEFORE your checks (it only defines functions).
# As each claimed check finishes, record its verdict:
#     record_verdict "<validation_will_run entry, verbatim>" <pass|fail|skip>
# Which checks run is your judgment (TARBALL.md 7.2); this epilogue
# mechanizes the reconciliation shape only. Diagnostic, never
# gatekeeping: it neither sets nor reads exit_code (7.3, 7.5).

declare -A BALE_VERDICTS=()

record_verdict() {
  BALE_VERDICTS["$1"]="$2"
}

reconcile_claims() {
  local manifest=".bale-manifest.json"
  if [ ! -f "$manifest" ]; then
    echo "[SKIP] claims reconciliation: $manifest not found (not in bale staging)"
    return 0
  fi
  local pairs=()
  local label
  if [ "${#BALE_VERDICTS[@]}" -gt 0 ]; then
    for label in "${!BALE_VERDICTS[@]}"; do
      pairs+=("$label=${BALE_VERDICTS[$label]}")
    done
  fi
  python3 - "$manifest" ${pairs[@]+"${pairs[@]}"} <<'BALE_RECONCILE'
import json, sys

manifest_path, *pairs = sys.argv[1:]
with open(manifest_path, encoding="utf-8") as fh:
    claims = json.load(fh).get("claims") or {}
verdicts = dict(p.rsplit("=", 1) for p in pairs)
print("claims vs verdict:")
if not claims:
    print("  (no claims in the manifest)")
    raise SystemExit(0)
# Label column is capped (fold-in: 008's accepted proposal): one
# pathological label must not drag every row's alignment out. A label
# past the cap still prints in full — identifiers are verbatim, never
# truncated — and only its own row overflows the column.
width = min(max(len(c) for c in claims) + 1, 40)
for check, claim in claims.items():
    if isinstance(claim, dict):
        # The v0.4.7 annotated carrier: {"value": ..., "claim_basis": ...}.
        # Reconcile against the value; the basis rides the manifest's
        # verbatim promotion into telemetry, not this block, so the
        # printed line keeps the exact shape the parser expects.
        claim = claim.get("value", "?")
    verdict = verdicts.get(check, "missing")
    if claim in ("untested", "unknown") or verdict in ("skip", "missing"):
        tag = "[n/a]"
    elif claim == verdict:
        tag = "[agree]"
    else:
        tag = "[DISAGREE]"
    name = check + ":"
    print(f"  {name:<{width}} claim={claim:<9} verdict={verdict:<8} {tag}")
BALE_RECONCILE
}
"""

# The final line of the epilogue emission: the call site the worker
# pastes after the last check. Separate from the definitions above so
# the placement instruction can sit beside it.
RECONCILE_CALL = """\
# --- claims reconciliation call (crafted; TARBALL.md 7.3) ---
# Paste this AFTER every check has recorded its verdict — last thing
# before the exit.
reconcile_claims
"""


def slug_problem(slug: str) -> str | None:
    """Return a human-readable objection to a probe slug, or None.

    Session slugs are short and kebab-cased (TARBALL.md §1). The slug
    lands inside bash comments and double-quoted strings, so anything
    outside kebab-case is refused rather than escaped — hygiene, not
    quoting cleverness.
    """
    if not slug or not slug.strip():
        return "empty slug"
    kebab = set("abcdefghijklmnopqrstuvwxyz0123456789-")
    ok = all(c in kebab for c in slug) \
        and not slug.startswith("-") and not slug.endswith("-") \
        and "--" not in slug
    if not ok:
        return (f"slug {slug!r} is not kebab-case — lowercase letters, "
                "digits, and single hyphens only (TARBALL.md 1)")
    return None


def log(msg: str) -> None:
    """All operational output goes to stderr; stdout carries the payload."""
    print(f"[craft] {msg}", file=sys.stderr)


def die(msg: str) -> "int":
    log(f"error: {msg}")
    return EXIT_ERROR


# ---------------------------------------------------------------------------
# Probe clipboard config (the opt-in epilogue's key)
# ---------------------------------------------------------------------------

def read_clipboard_command(base: Path | None = None) -> tuple[str | None, str]:
    """Read the opt-in `[probe] clipboard_command` from bale.toml.

    Returns (command, note): command is the configured one-line shell
    command, or None whenever the key is unreadable for any reason —
    no file, no section, no key, or a value outside the minimal shape
    this reader supports. The note says which, for the emission log.

    Deliberately a minimal single-key scan, not a TOML parser: this
    tool is stdlib-only and runs standalone on 3.10 (no tomllib), and
    the key's contract is one section, one key, one quoted one-line
    basic string with no escapes. Anything richer is treated as unset
    — the never-fails, never-silently-skips path: the scaffold then
    carries remedy text instead of the epilogue. The config-side
    accessor that eventually lands in bin/bale_config.py is the full
    reader; this scan must agree with it on the simple shape.

    Lookup order: ./bale.toml (the repo-root layout), then
    ./context/bale.toml (the request-root layout). The first file
    found settles it — the two are alternative locations for the same
    project-layer file, not config layers.
    """
    root = base if base is not None else Path.cwd()
    for rel in CLIPBOARD_CONFIG_CANDIDATES:
        path = root / rel
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            return None, f"{rel} exists but is unreadable ({e})"
        section = None
        for raw in text.splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("[") and line.endswith("]"):
                section = line[1:-1].strip()
                continue
            if section != CLIPBOARD_SECTION or "=" not in line:
                continue
            key, _, value = line.partition("=")
            if key.strip() != CLIPBOARD_KEY:
                continue
            value = value.strip()
            # Minimal basic-string read: "cmd", optional trailing
            # comment, no escapes and no embedded quotes supported.
            if value.startswith('"'):
                closing = value.find('"', 1)
                if closing > 0:
                    cmd = value[1:closing].strip()
                    rest = value[closing + 1:].strip()
                    usable = (cmd and "\\" not in cmd
                              and (not rest or rest.startswith("#")))
                    if usable:
                        return cmd, (f"{rel} sets [{CLIPBOARD_SECTION}] "
                                     f"{CLIPBOARD_KEY}")
            return None, (f"{rel} carries [{CLIPBOARD_SECTION}] "
                          f"{CLIPBOARD_KEY} but not as a non-empty "
                          f"one-line quoted string without escapes — "
                          f"treated as unset")
        return None, (f"{rel} found; [{CLIPBOARD_SECTION}] "
                      f"{CLIPBOARD_KEY} unset")
    return None, (f"no bale.toml found "
                  f"({', '.join('./' + c for c in CLIPBOARD_CONFIG_CANDIDATES)})")


def build_probe_scaffold(slug: str, clipboard_cmd: str | None) -> str:
    """The full --probe emission: the fixed skeleton plus one of the
    two clipboard tails — the epilogue when a command is configured,
    the remedy text when it is not. One of the two always emits; the
    epilogue never touches stdout (status lines go to stderr) and
    never affects the probe's exit."""
    body = PROBE_SCAFFOLD.format(slug=slug)
    if clipboard_cmd is not None:
        return body + "\n" + PROBE_CLIPBOARD_EPILOGUE.format(
            clip=clipboard_cmd)
    return body + "\n" + PROBE_CLIPBOARD_REMEDY


# ---------------------------------------------------------------------------
# Planner-bundle emission (--bundle; board 49b)
# ---------------------------------------------------------------------------

def normalize_member(data: bytes) -> bytes:
    """Every CRLF read as LF — the bundle format's own normalization
    rule, applied at write so the archived bytes ARE the hashed bytes.

    Mirrors the consumer's normalize_bundle_member (bin/bale_open.py)
    by contract: both are the format rule's one-line application, and
    the round-trip tests pin the agreement. Scoped to bundle members;
    nothing else in this tool normalizes line endings.
    """
    return data.replace(b"\r\n", b"\n")


def bundle_stem_problem(stem: str) -> str | None:
    """Return a human-readable objection to a bundle stem, or None.

    The stem lands in a filename, the printed `bale open` line, and
    the tar member-adjacent tooling; the recommended shape is
    `<date>-<slug>` — kebab throughout, same hygiene as probe slugs.
    The path knob is --out-dir, never the stem.
    """
    if not stem or not stem.strip():
        return "empty stem"
    if "/" in stem or "\\" in stem:
        return (f"stem {stem!r} contains a path separator — the stem "
                "names the file; --out-dir names where it lands")
    if stem.endswith(BUNDLE_SUFFIX):
        return (f"stem {stem!r} already ends with {BUNDLE_SUFFIX!r} — "
                "pass the bare stem; the tool appends the reserved "
                "suffix")
    kebab = set("abcdefghijklmnopqrstuvwxyz0123456789-")
    ok = all(c in kebab for c in stem) \
        and not stem.startswith("-") and not stem.endswith("-") \
        and "--" not in stem
    if not ok:
        return (f"stem {stem!r} is not kebab-case — lowercase letters, "
                "digits, and single hyphens only (recommended shape: "
                "<date>-<slug>)")
    return None


def pack_arg_problem(token: str, index: int) -> str | None:
    """Return a human-readable objection to one stored pack-argv
    token, or None. Argument hygiene mirroring the consumer-side
    manifest gate (validate_bundle_manifest) so a defective argv
    fails at the desk, where the fix is immediate:

    - the delivery flags are never stored (bare or =-glued) — the
      consumer injects them from member presence, the single source;
    - the array is the vector AFTER the pack subcommand, so a leading
      'pack' token is a composition error;
    - `--no-readme` is likewise never stored: a null brief slot is
      the one spelling of no-brief, and the consumer injects the
      flag from it (emitter-side hygiene past the gate — flagged as
      such where this tool's docs name it).
    """
    if not token:
        return f"pack_argv[{index}] is empty — every token is non-empty"
    for banned in DELIVERY_FLAGS:
        if token == banned or token.startswith(banned + "="):
            return (f"pack_argv[{index}] carries the delivery flag "
                    f"{banned} — the consumer injects it from member "
                    f"presence (--brief / --checkpoint are this "
                    f"tool's spellings); never store it")
    if token == "--no-readme":
        return (f"pack_argv[{index}] carries --no-readme — a no-brief "
                "bundle is spelled --no-brief here, and the consumer "
                "injects the flag from the null brief slot")
    if index == 0 and token == "pack":
        return ("pack_argv[0] is 'pack' — the array is the argument "
                "vector AFTER the pack subcommand; drop the verb")
    return None


def parse_intent(spec: str) -> tuple[str, str] | str:
    """Parse one --pre-answered PROMPT=SUBJECT; return the pair or a
    human-readable objection string. The prompt vocabulary is CLOSED
    (INTENT_PROMPTS — one prompt, one subject, never a blanket yes)."""
    prompt, sep, subject = spec.partition("=")
    if not sep:
        return (f"--pre-answered {spec!r} is not PROMPT=SUBJECT — an "
                "intent names exactly one prompt and one subject")
    prompt = prompt.strip()
    subject = subject.strip()
    if prompt not in INTENT_PROMPTS:
        return (f"--pre-answered names unknown prompt {prompt!r} — the "
                f"vocabulary is closed: {', '.join(INTENT_PROMPTS)}")
    if not subject:
        return (f"--pre-answered {spec!r} has an empty subject — for "
                "'supersede' the subject is the parent session id")
    return prompt, subject


def build_bundle_manifest(pack_args: list[str],
                          brief: bytes | None,
                          checkpoint: bytes | None,
                          intents: list[tuple[str, str]]) -> dict:
    """bundle.json: the four required keys, hashes computed from the
    LF-normalized member bytes handed in (never transcribed). Both
    member slots are always present — an object when the member
    ships, an explicit null when it does not (the uniform shape)."""
    def slot(name: str, data: bytes | None) -> dict | None:
        if data is None:
            return None
        return {"path": name,
                "sha256": hashlib.sha256(data).hexdigest()}
    return {
        "bundle_format": 1,
        "pack_argv": list(pack_args),
        "members": {
            "brief": slot(BRIEF_MEMBER, brief),
            "checkpoint": slot(CHECKPOINT_MEMBER, checkpoint),
        },
        "pre_answered": [{"prompt": p, "subject": s}
                         for p, s in intents],
    }


def bundle_archive_bytes(manifest: dict,
                         members: dict[str, bytes]) -> bytes:
    """The bundle container: a gzipped tar, members flat at the
    archive root — bundle.json plus exactly the declared members, in
    a stable order. Deterministic on purpose (fixed tar metadata,
    zeroed gzip mtime, no embedded filename): identical inputs yield
    identical bytes, which is what makes the idempotent re-run
    checkable and desk-side diffs meaningful."""
    payload: list[tuple[str, bytes]] = [
        ("bundle.json",
         json.dumps(manifest, indent=2).encode("utf-8") + b"\n"),
    ]
    payload += sorted(members.items())
    buf = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buf, mtime=0) as gz:
        with tarfile.open(fileobj=gz, mode="w") as tf:
            for name, data in payload:
                info = tarfile.TarInfo(name)
                info.size = len(data)
                info.mtime = 0
                info.mode = 0o644
                info.uid = info.gid = 0
                info.uname = info.gname = ""
                tf.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def read_bundle_input(label: str, path_str: str) -> bytes | str:
    """Read one member input file for --bundle; return its raw bytes
    or a human-readable objection string. Same loud posture as pack's
    own file-delivery flags: a missing, unreadable, or empty file
    refuses — a bundle carrying a hollow member helps nobody."""
    path = Path(path_str)
    if not path.is_file():
        return f"{label}: not a file: {path}"
    try:
        data = path.read_bytes()
    except OSError as e:
        return f"{label}: unreadable: {e}"
    if not data.strip():
        return f"{label}: {path} is empty — a hollow member never ships"
    return data


# ---------------------------------------------------------------------------
# Exchange block emission (--emit-block; the worker side of the thread)
# ---------------------------------------------------------------------------
#
# The worker's half of the exchange thread (TARBALL.md §5.9.2; ADR-0017).
# `bale relay` renders the counterpart-facing paste block for every record
# it ingests — but relay runs in the PLANNER's repo, against a suspended
# session's `.bale/` state, and the worker has neither. So the block the
# worker hands the courier is rendered here, and the two renderings have
# to be the same bytes: the trailer's sha256 is computed over the body,
# ingest recomputes it over the bytes it read, and a body that serializes
# even slightly differently on this side is a truncated-paste refusal on
# the other.
#
# Everything below is RE-DECLARED from `bin/bale` section 29 (the
# sentinels, the body serialization, the header layout) and from
# bin/bale_validate.py (the closed vocabularies and the record's
# structural rules) — the INTENT_PROMPTS precedent above, for the same
# reason, one size larger. This tool imports nothing from bale because it
# runs in a worker session where no bale install exists; and there is no
# schema file to fall back on either, because TARBALL.md §3.1 injects
# exactly the five global docs and the two tools into a request. A
# project's own `schemas/` reaches `context/` only when its packer names
# it, and §3.1 permits even that copy to be a partial extract. A lookup
# would therefore work in the bale-src repo and nowhere else, which is
# worse than no lookup at all.
#
# Two homes without a pin is how citations drift, so the duplication
# carries the drift guard the bundle constants carry, widened to match
# what is duplicated: tests/test_craft_response.py's ExchangeBlockParity
# renders both implementations over a fixture corpus and compares BYTES,
# pins these constants against section 29's, and asserts the structural
# checks below verdict-for-verdict against validate_exchange_record and
# validate_clarification_questions over a shared pass/fail corpus. A
# session changing either home changes both in the same response.

EXCHANGE_BLOCK_BEGIN = "BALE EXCHANGE BEGIN"
EXCHANGE_BLOCK_END = "BALE EXCHANGE END"
EXCHANGE_TRAILER_LABEL = "# sha256"

EXCHANGE_SIDE_WORKER = "worker"
EXCHANGE_SIDE_PLANNER = "planner"
EXCHANGE_SIDES = (EXCHANGE_SIDE_WORKER, EXCHANGE_SIDE_PLANNER)

# The record_version exchange-record.schema.json pins to exactly 1, and
# the two closed vocabularies validate_exchange_record enforces record-
# wide at any depth.
EXCHANGE_RECORD_VERSION = 1
ANSWER_DISPOSITIONS = ("as-recommended", "option", "free-text")
QUESTION_PRIORITIES = ("blocking", "batched")

# The body serialization parameters, which are the byte-parity surface:
# two-space indent and ASCII escaping (json.dumps' default ensure_ascii),
# one trailing newline. ASCII escaping is the transport-proof spelling —
# a chat or mail hop cannot mangle a non-ASCII character the body never
# carries — and it is why the parity test pins the parameter rather than
# trusting two call sites to keep defaulting the same way.
EXCHANGE_BODY_INDENT = 2

# The exchange record's envelope, and the answer row's closed field set
# (additionalProperties: false at that level, unlike the loose envelope).
EXCHANGE_ENVELOPE_KEYS = ("record_version", "session_id", "round", "from",
                          "created_at")
ANSWER_REQUIRED_KEYS = ("question_round", "question_index", "answer",
                        "disposition")
ANSWER_OPTIONAL_KEYS = ("amendment_target",)

# The question row: the four legacy fields plus the three v0.4.7 additive
# ones. QUESTION_STUB_KEYS above is the required half — the seeded stub's
# home — and this is the full permitted set, so the two cannot disagree
# about what a filled row may carry.
QUESTION_OPTIONAL_KEYS = ("options", "recommendation", "priority")

CLARIFICATION_KIND = "clarification"


def exchange_body_bytes(record: dict) -> bytes:
    """The paste block's body for `record` — re-declared from section
    29's _exchange_body_bytes.

    The trailer's sha256 is computed over exactly these bytes, and
    ingest recomputes over exactly the bytes it read between header and
    trailer, so any truncation or edit in transit refuses.
    """
    return (json.dumps(record, indent=EXCHANGE_BODY_INDENT) + "\n").encode(
        "utf-8")


def format_exchange_block(sid: str, record: dict) -> str:
    """Render the counterpart-facing paste block — re-declared from
    section 29's format_exchange_block, byte for byte:

      BALE EXCHANGE BEGIN <sid>          sentinel (self-delimiting)
      # ... purpose header ...           direction and round, who reads it
      { ...record JSON... }              the body
      # sha256 <hex>                     integrity trailer over the body
      BALE EXCHANGE END                  sentinel

    Both direction branches are mirrored even though the crafter emits
    only the worker side (a `from: planner` record refuses at the CLI —
    the planner's side of the thread comes from `bale relay`). A partial
    mirror would leave half the layout unpinned by the parity suite and
    would diverge silently the first time someone rendered the other
    direction; the policy belongs at the gate, not in a hole in the
    renderer. Pure: the tests render and re-parse it in memory.
    """
    side = record.get("from")
    rnd = record.get("round")
    to_side = (EXCHANGE_SIDE_PLANNER if side == EXCHANGE_SIDE_WORKER
               else EXCHANGE_SIDE_WORKER)
    n_q = len(record.get("questions") or [])
    n_a = len(record.get("answers") or [])
    body = exchange_body_bytes(record)
    digest = hashlib.sha256(body).hexdigest()
    header = [
        f"{EXCHANGE_BLOCK_BEGIN} {sid}",
        f"# bale exchange record — session {sid} — round {rnd} — "
        f"from {side} to {to_side}",
    ]
    if side == EXCHANGE_SIDE_WORKER:
        header.append(
            f"# {n_q} blocking question(s)"
            + (f" and {n_a} answer(s)" if n_a else "")
            + ". Planner: answer as an exchange record (from: planner,"
            f" round {rnd + 1 if isinstance(rnd, int) else '<next>'},"
            f" answers[] keyed question_round {rnd}) and record it with"
            f" `bale relay {sid} <answer.json|->`.")
    else:
        header.append(
            f"# {n_a} answer(s)"
            + (f" and {n_q} question(s) asked back" if n_q else "")
            + f". Worker: read the record, continue under {sid}, and"
            " ship the normal response the clarification deferred"
            + (" — or answer the questions asked back as the next"
               " round." if n_q else "."))
    header.append(
        "# Body: the record (exchange-record.schema.json). Trailer: sha256 "
        "of the body bytes — a mismatch on ingest means a truncated paste; "
        "re-request the block rather than reason from it.")
    return ("\n".join(header) + "\n"
            + body.decode("utf-8")
            + f"{EXCHANGE_TRAILER_LABEL} {digest}\n"
            + f"{EXCHANGE_BLOCK_END}\n")


def normalize_manifest_to_record(manifest: dict, sid: str, rnd: int,
                                 created_at: str) -> dict:
    """The clarification manifest's reading as an exchange record —
    re-declared from section 29's _normalize_manifest_to_record.

    Key insertion order is load-bearing: json.dumps preserves it, so the
    body's bytes (and therefore the trailer) depend on it matching
    section 29's dict literal exactly.

    Two fields differ in PROVENANCE from relay's, not in shape. `round`
    is the worker's `--round` rather than the thread's next NNN — the
    worker has no thread directory to count — and `created_at` is
    stamped at emission rather than copied from the preserved sidecar,
    for the same reason. Both land in the same slots with the same
    spelling, so the record relay would have built and the record this
    builds are the same record whenever the round agrees.
    """
    return {
        "record_version": EXCHANGE_RECORD_VERSION,
        "session_id": sid,
        "round": rnd,
        "from": EXCHANGE_SIDE_WORKER,
        "created_at": created_at,
        "questions": list(manifest.get("questions") or []),
    }


def emission_stamp() -> str:
    """The `created_at` stamp for a record built at emission: ISO 8601
    with a zero UTC offset, seconds precision — the spelling
    preserve_clarification_record uses for `preserved_at`, so the two
    provenances of the same slot read identically."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _created_at_problem(value) -> str | None:
    """Why `value` is not an ISO 8601 UTC timestamp, or None.

    Re-declared from bale_validate._created_at_problem, including its
    asymmetry: a non-string returns None here because the envelope check
    has already reported the type, exactly as the schema pass does
    there. Accepted: anything datetime.fromisoformat parses that carries
    a zero UTC offset — `...+00:00` or the `Z` suffix, mapped before
    parsing since 3.10's fromisoformat does not accept it.
    """
    from datetime import datetime, timezone
    if not isinstance(value, str):
        return None
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return (f"{value!r} is not an ISO 8601 timestamp (expected e.g. "
                f"2026-08-29T14:03:00+00:00)")
    if parsed.tzinfo is None:
        return (f"{value!r} carries no UTC offset — created_at is ISO 8601 "
                f"UTC (append +00:00 or Z)")
    if parsed.utcoffset() != timezone.utc.utcoffset(None):
        return (f"{value!r} is not in UTC — created_at carries a zero "
                f"offset (+00:00 or Z), never a local one")
    return None


def _is_int(value) -> bool:
    """JSON-Schema integer semantics: bool is a distinct type, so True is
    not 1 here even though Python says otherwise."""
    return isinstance(value, int) and not isinstance(value, bool)


def _nonempty_str(value) -> bool:
    return isinstance(value, str) and len(value) >= 1


def _walk_closed_vocabularies(value, path: str, checks: dict,
                              problems: list[str]) -> None:
    """Enforce closed vocabularies anywhere their keys appear — the
    record-wide backstop re-declared from bale_validate's walk of the
    same name.

    A schema's enums catch the spots the schema names; this catches an
    invented value at ANY depth, so a consumer that put the key
    somewhere the schema never enumerated gets the same verdict.
    """
    if isinstance(value, dict):
        for k, v in value.items():
            child = f"{path}.{k}" if path else str(k)
            check = checks.get(k)
            if check is not None:
                problem = check(v)
                if problem is not None:
                    problems.append(f"{child}: {problem}")
            _walk_closed_vocabularies(v, child, checks, problems)
    elif isinstance(value, list):
        for i, item in enumerate(value):
            _walk_closed_vocabularies(item, f"{path}[{i}]", checks, problems)


def _vocabulary_check(allowed: tuple, label: str):
    def check(v) -> str | None:
        if v not in allowed:
            return (f"{v!r} is not one of {list(allowed)} — the {label} "
                    f"vocabulary is closed, wherever the key appears")
        return None
    return check


def question_row_problems(rows) -> list[str]:
    """Structural check over clarification question rows; [] = valid.

    The crafter's stdlib-only twin of
    bale_validate.validate_clarification_questions, which derives the
    same rules from response-manifest.schema.json's questions.items. The
    row shape is the four required fields (QUESTION_STUB_KEYS — the
    seeded stub's home, reused here so the tool cannot seed a stub its
    own check would reject), the three additive v0.4.7 fields, and no
    others (additionalProperties: false at the row level). `options`,
    when present, is a non-empty array of non-empty strings; `priority`
    is the closed two-class vocabulary, enforced here at its named spot
    AND row-wide by the walk, matching the library's discipline.

    Messages are the crafter's own; only the VERDICT is pinned against
    the library, over the corpus in tests/test_craft_response.py.
    """
    if not isinstance(rows, list):
        return [f"questions: expected an array, got "
                f"{type(rows).__name__}"]
    problems: list[str] = []
    permitted = set(QUESTION_STUB_KEYS) | set(QUESTION_OPTIONAL_KEYS)
    for i, row in enumerate(rows):
        at = f"questions[{i}]"
        if not isinstance(row, dict):
            problems.append(f"{at}: expected an object, got "
                            f"{type(row).__name__}")
            continue
        for key in QUESTION_STUB_KEYS:
            if key not in row:
                problems.append(f"{at}: missing required key {key!r}")
            elif not _nonempty_str(row[key]):
                problems.append(f"{at}.{key}: expected a non-empty string")
        for key in sorted(set(row) - permitted):
            problems.append(f"{at}: unknown key {key!r}")
        if "options" in row:
            opts = row["options"]
            if not isinstance(opts, list):
                problems.append(f"{at}.options: expected an array")
            elif not opts:
                problems.append(f"{at}.options: at least one candidate when "
                                "the key is present")
            else:
                for j, opt in enumerate(opts):
                    if not _nonempty_str(opt):
                        problems.append(f"{at}.options[{j}]: expected a "
                                        "non-empty string")
        if "recommendation" in row and not _nonempty_str(row["recommendation"]):
            problems.append(f"{at}.recommendation: expected a non-empty "
                            "string")
        if "priority" in row and not isinstance(row["priority"], str):
            problems.append(f"{at}.priority: expected a string")
    _walk_closed_vocabularies(
        rows, "questions",
        {"priority": _vocabulary_check(QUESTION_PRIORITIES,
                                       "question priority")},
        problems)
    return problems


def exchange_record_problems(record) -> list[str]:
    """Structural check over one exchange record; [] = valid.

    The crafter's stdlib-only twin of
    bale_validate.validate_exchange_record, layer for layer:

    1. **Envelope** — the five required keys, record_version exactly 1,
       session_id a non-empty string, round an integer >= 1, from in the
       closed side vocabulary, created_at a non-empty string. Loose
       otherwise (additionalProperties: true), so the preserved copy's
       `preserved_at` sidecar and future additive fields validate.
    2. **Question rows, by reference** — delegated to
       question_row_problems, so a row that validates inside a
       clarification manifest validates here and vice versa.
    3. **The closed-vocabulary walk** — `from` and `disposition` at any
       depth.
    4. **The rules a schema cannot express** — at least one of
       questions[] / answers[] non-empty; created_at ISO 8601 UTC; every
       answer's question_round strictly earlier than this record's round.

    What it deliberately does NOT check is the thread-level half:
    whether a (question_round, question_index) resolves to a preserved
    question needs the thread, which no library validator has and the
    worker has less of. That check is relay's, on ingest — so a record
    this accepts can still be refused there, on a fact this side cannot
    see. Everything the library checks WITHOUT the thread, this checks,
    and the corpus in tests/test_craft_response.py pins the agreement.
    """
    if not isinstance(record, dict):
        return [f"exchange record is not a JSON object "
                f"(got {type(record).__name__})"]
    problems: list[str] = []

    for key in EXCHANGE_ENVELOPE_KEYS:
        if key not in record:
            problems.append(f"<root>: missing required key {key!r}")
    if "record_version" in record:
        if record["record_version"] != EXCHANGE_RECORD_VERSION \
                or not _is_int(record["record_version"]):
            problems.append(
                f"record_version: expected exactly "
                f"{EXCHANGE_RECORD_VERSION}, got "
                f"{record['record_version']!r}")
    if "session_id" in record and not _nonempty_str(record["session_id"]):
        problems.append("session_id: expected a non-empty string")
    rnd = record.get("round")
    if "round" in record and (not _is_int(rnd) or rnd < 1):
        problems.append(f"round: expected an integer >= 1, got {rnd!r}")
    if "created_at" in record and not _nonempty_str(record["created_at"]):
        problems.append("created_at: expected a non-empty string")

    questions = record.get("questions")
    if questions is not None:
        if not isinstance(questions, list):
            problems.append("questions: expected an array")
        else:
            problems.extend(question_row_problems(questions))

    answers = record.get("answers")
    if answers is not None and not isinstance(answers, list):
        problems.append("answers: expected an array")
    elif isinstance(answers, list):
        permitted = set(ANSWER_REQUIRED_KEYS) | set(ANSWER_OPTIONAL_KEYS)
        for i, row in enumerate(answers):
            at = f"answers[{i}]"
            if not isinstance(row, dict):
                problems.append(f"{at}: expected an object, got "
                                f"{type(row).__name__}")
                continue
            for key in ANSWER_REQUIRED_KEYS:
                if key not in row:
                    problems.append(f"{at}: missing required key {key!r}")
            for key in sorted(set(row) - permitted):
                problems.append(f"{at}: unknown key {key!r}")
            qr = row.get("question_round")
            if "question_round" in row and (not _is_int(qr) or qr < 1):
                problems.append(f"{at}.question_round: expected an integer "
                                f">= 1, got {qr!r}")
            qi = row.get("question_index")
            if "question_index" in row and (not _is_int(qi) or qi < 0):
                problems.append(f"{at}.question_index: expected an integer "
                                f">= 0, got {qi!r}")
            if "answer" in row and not _nonempty_str(row["answer"]):
                problems.append(f"{at}.answer: expected a non-empty string")
            if "disposition" in row and not isinstance(row["disposition"],
                                                       str):
                problems.append(f"{at}.disposition: expected a string")
            if "amendment_target" in row \
                    and not _nonempty_str(row["amendment_target"]):
                problems.append(f"{at}.amendment_target: expected a "
                                "non-empty string")
            if _is_int(qr) and _is_int(rnd) and qr >= rnd:
                problems.append(
                    f"{at}.question_round: {qr} is not an earlier round "
                    f"than this record's round {rnd} — an answer keys a "
                    f"question already in the thread")

    _walk_closed_vocabularies(
        record, "",
        {"from": _vocabulary_check(EXCHANGE_SIDES, "exchange side"),
         "disposition": _vocabulary_check(ANSWER_DISPOSITIONS,
                                          "answer disposition")},
        problems)

    has_questions = isinstance(questions, list) and len(questions) > 0
    has_answers = isinstance(answers, list) and len(answers) > 0
    if not has_questions and not has_answers:
        problems.append(
            "<root>: at least one of questions[] / answers[] must be "
            "non-empty — an exchange record with nothing asked and "
            "nothing answered is not a round")

    problem = _created_at_problem(record.get("created_at"))
    if problem is not None:
        problems.append(f"created_at: {problem}")
    return problems


def read_emit_block_input(path_str: str) -> bytes | str:
    """Read the --emit-block input: stdin for `-`, else the named file.
    Returns bytes, or an error message string.

    Deliberately not a search-path resolution (relay's `_read_relay_input`
    consults the project's apply search paths): those paths come from a
    project's bale config, which a worker session has no install to read.
    The worker names the file it just filled, in its own directory.
    """
    if path_str == "-":
        try:
            return sys.stdin.buffer.read()
        except OSError as exc:
            return f"--emit-block: could not read the record from stdin: {exc}"
    src = Path(path_str)
    if not src.is_file():
        return f"--emit-block: file not found: {src}"
    try:
        return src.read_bytes()
    except OSError as exc:
        return f"--emit-block: could not read {src}: {exc}"


def build_emit_block(data: bytes, round_arg: int | None) -> tuple[str, str]:
    """Turn the read bytes into (block, log line), or raise ValueError
    with the refusal message.

    Input detection follows relay's, deliberately: a `response_kind:
    "clarification"` object is a filled clarification manifest and takes
    the normalization path; anything else is read as an exchange record
    and is emitted as-is once it validates. Both refuse rather than
    rewrite when the worker's `--round` contradicts what the input
    already says.
    """
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"--emit-block: input is not valid UTF-8: {exc}")
    if not text.strip():
        raise ValueError(
            "--emit-block: input is empty — expected a filled clarification "
            "manifest or a filled worker exchange record")
    try:
        record = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"--emit-block: input is not valid JSON: {exc}")
    if not isinstance(record, dict):
        raise ValueError(
            f"--emit-block: input is not a JSON object (got "
            f"{type(record).__name__})")

    if record.get("response_kind") == CLARIFICATION_KIND:
        sid = record.get("session_id")
        if not _nonempty_str(sid):
            raise ValueError(
                "--emit-block: the clarification manifest carries no "
                "session_id — the sentinel line and the record's own "
                "session_id both come from it, and a block pasted against "
                "the wrong session must refuse on the sentinel")
        rnd = 1 if round_arg is None else round_arg
        body_record = normalize_manifest_to_record(record, sid, rnd,
                                                   emission_stamp())
        problems = exchange_record_problems(body_record)
        if problems:
            raise ValueError(
                "--emit-block: the clarification manifest does not read as "
                "a valid exchange record; nothing emitted:\n  "
                + "\n  ".join(problems))
        return (format_exchange_block(sid, body_record),
                f"clarification manifest normalized to a from: worker "
                f"record, round {rnd}, "
                f"{len(body_record['questions'])} question(s)")

    if "from" not in record:
        raise ValueError(
            "--emit-block: input is neither a clarification manifest "
            "(response_kind: \"clarification\") nor an exchange record (a "
            "`from` key) — the two shapes relay accepts are the two shapes "
            "emitted here")
    if record["from"] != EXCHANGE_SIDE_WORKER:
        raise ValueError(
            f"--emit-block: the record is from {record['from']!r}; the "
            f"crafter emits the worker side of the thread only. The "
            f"planner's side is emitted by `bale relay <sid> "
            f"<answer.json|->` in the planner's repo, which has the "
            f"suspended session's thread to sequence it against.")
    rnd = record.get("round")
    if round_arg is not None and rnd != round_arg:
        raise ValueError(
            f"--emit-block: --round {round_arg} contradicts the record's "
            f"own round {rnd!r} — the round is the record's fact and this "
            f"flag does not rewrite it; drop --round, or fix the record")
    sid = record.get("session_id")
    if not _nonempty_str(sid):
        raise ValueError(
            "--emit-block: the exchange record carries no session_id — the "
            "sentinel line comes from it, and a block pasted against the "
            "wrong session must refuse on the sentinel")
    problems = exchange_record_problems(record)
    if problems:
        raise ValueError(
            "--emit-block: the exchange record is not valid "
            "(exchange-record.schema.json); nothing emitted:\n  "
            + "\n  ".join(problems))
    return (format_exchange_block(sid, record),
            f"worker exchange record emitted as-is, round {rnd}, "
            f"{len(record.get('questions') or [])} question(s) and "
            f"{len(record.get('answers') or [])} answer(s)")


# ---------------------------------------------------------------------------
# Path handling
# ---------------------------------------------------------------------------

def rel_path_problem(path_str: str) -> str | None:
    """Return a human-readable objection to a worker-supplied repo-relative
    path, or None when the path is usable. Catches the typo shapes that
    would otherwise scaffold a wrong (or dangerous) apply.sh line."""
    if not path_str or not path_str.strip():
        return "empty path"
    if path_str != path_str.strip():
        return f"leading/trailing whitespace in {path_str!r}"
    if "\\" in path_str:
        return f"backslash in {path_str!r} — manifest paths are POSIX"
    if path_str.startswith("/"):
        return f"absolute path {path_str!r} — paths are repo-relative"
    if path_str.endswith("/"):
        return f"trailing slash in {path_str!r} — entries name files"
    parts = PurePosixPath(path_str).parts
    if "." in parts or ".." in parts:
        return f"'.' or '..' segment in {path_str!r}"
    if parts and parts[0] == "files":
        return (
            f"{path_str!r} starts with 'files/' — pass the repo-relative "
            "path; the mirror prefix is the tool's to strip"
        )
    return None


def walk_mirror(files_root: Path) -> list[str]:
    """Enumerate the files/ mirror as sorted repo-relative POSIX paths.

    Directories are not entries (the mirror is enumerated by its files,
    TARBALL.md §5.1); a broken symlink is an error, never a silent skip.
    """
    found: list[str] = []
    for p in sorted(files_root.rglob("*")):
        if p.is_dir():
            continue
        if p.is_symlink() and not p.exists():
            raise ValueError(
                f"broken symlink under files/: {p.relative_to(files_root).as_posix()}"
            )
        if p.is_file():
            found.append(p.relative_to(files_root).as_posix())
            continue
        raise ValueError(
            f"unsupported entry under files/ (not a regular file): "
            f"{p.relative_to(files_root).as_posix()}"
        )
    return sorted(found)


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Skeleton construction
# ---------------------------------------------------------------------------

def build_changes(files_root: Path | None, deleted: list[str]) -> list[dict]:
    """The changes[] skeleton: computed values filled, judgment left empty.

    Mirror entries first (sorted), then deleted stubs (sorted) — a stable
    order so re-runs diff cleanly.
    """
    entries: list[dict] = []
    mirror_paths: list[str] = []
    if files_root is not None and files_root.is_dir():
        mirror_paths = walk_mirror(files_root)
    for rel in mirror_paths:
        f = files_root / rel  # type: ignore[operator]
        entries.append({
            "path": rel,
            "action": "",      # worker fills: created | modified
            "reason": "",      # worker fills: judgment, never generated
            "size_bytes": f.stat().st_size,
            "sha256": sha256_of(f),
        })
    for rel in sorted(deleted):
        entries.append({
            "path": rel,
            "action": "deleted",
            "reason": "",      # worker fills: judgment, never generated
            "size_bytes": 0,
            "sha256": None,
        })
    return entries


def build_manifest(sid: str, kind: str, changes: list[dict],
                   n_questions: int = 0) -> dict:
    """The manifest skeleton per TARBALL.md §5.2 (normal), §5.6.2
    (bailout), or §5.9.2 (clarification): computed and mechanical fields
    filled, judgment fields present but empty.

    The two non-normal kinds carry the empty change surfaces their
    sections require; a clarification additionally seeds `questions[]`
    with all-empty four-field entry stubs (unfilled-cannot-pass: the
    lint rejects the empty strings).
    """
    manifest = {
        "session_id": sid,
        "responds_to": sid,
        "corrects": None,
        "response_kind": kind,
        "summary": "",              # worker fills
        "changes": changes if kind == "normal" else [],
        "deferred": [],
        "validation_will_run": [],  # worker fills (normal kind)
        "claims": {},               # worker fills (normal kind)
    }
    if kind == "clarification":
        manifest["questions"] = [
            {k: "" for k in QUESTION_STUB_KEYS}  # worker fills all four
            for _ in range(n_questions)
        ]
    return manifest


def build_diagnostics(sid: str) -> dict:
    """The diagnostics.json skeleton per TARBALL.md §5.8 /
    schemas/diagnostics.schema.json: exactly the schema's required keys.
    `session_id` is mechanical (the tool has it from --sid); every other
    value is empty and the worker's — an unfilled skeleton is
    deliberately schema-invalid (`bail_trigger` off-enum,
    `bail_narrative` empty), so it cannot pass the lint by accident.
    """
    return {
        "session_id": sid,
        "bail_trigger": "",         # worker fills: an enum value (§5.8)
        "bail_narrative": "",       # worker fills: judgment
        "context_loaded": [],       # worker fills
        "exploration_paths": [],    # worker fills
        "tool_calls_summary": {},   # worker fills
        "what_would_save_next_time": [],  # worker fills
    }


def build_apply_sh(deleted: list[str], executables: list[str]) -> str:
    """The apply.sh scaffold per TARBALL.md §5.1.1: the verbatim no-op when
    nothing needs the script, otherwise rm lines then chmod lines (chmod
    runs after the overlay applies, so it comes last)."""
    if not deleted and not executables:
        return APPLY_NOOP
    lines = [APPLY_HEADER]
    for rel in sorted(deleted):
        lines.append(f"# Remove {rel} — TODO(worker): one-line reason.")
        lines.append(f"rm -f {shell_quote(rel)}")
        lines.append("")
    if executables:
        lines.append(
            "# Restore executable bits the files/ overlay strips "
            "(TARBALL.md 5.1.1)."
        )
        for rel in sorted(executables):
            lines.append(f"chmod +x {shell_quote(rel)}")
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def build_exec_assertions(executables: list[str]) -> str:
    """The §7.7 exec-bit assertion block, one per named executable.

    Generated from the SAME list build_apply_sh turns into chmod lines
    — one source, two emissions, so within an invocation the chmod line
    and its assertion cannot disagree. Same sorted order as the chmod
    lines, for the same clean-rediff reason. Empty list emits nothing:
    a session shipping no executables omits the assertion (§7.7).
    """
    if not executables:
        return ""
    lines = [
        "# --- exec-bit assertions (crafted; TARBALL.md 7.7) ---",
        "# Paste with your session-specific assertions (7.2 item 6).",
        "# Generated from the same --executable list as apply.sh's chmod",
        "# lines (5.1.1) — re-emit both if the list changes. Assumes the",
        "# enclosing script tracks failures in exit_code and exits with it.",
    ]
    for rel in sorted(executables):
        q = shell_quote(rel)
        lines += [
            f"if [ -x {q} ]; then",
            f"  echo {shell_quote(f'[PASS] {rel} is executable')}",
            "else",
            f"  echo {shell_quote(f'[FAIL] {rel} not executable — apply.sh chmod omitted?')}",
            "  exit_code=1",
            "fi",
        ]
    return "\n".join(lines) + "\n"


def build_validation_epilogue(executables: list[str],
                              fragment: str | None = None) -> str:
    """The --validation-epilogue emission.

    Combined (fragment=None, the historical shape): reconciliation
    definitions, exec-bit assertions (when any), and the call site —
    each part carrying its own paste-placement instruction, the worker
    cutting at the banners.

    Separable (fold-in: board-13c via the registry): `--fragment`
    emits exactly one part, so each can be pasted straight where its
    instruction says — `definitions` before the checks, `assertions`
    with the session-specific assertions, `call` last — and pasting
    the definitions block can never fire `reconcile_claims` early.
    """
    if fragment == "definitions":
        return RECONCILE_EPILOGUE
    if fragment == "assertions":
        return build_exec_assertions(executables)
    if fragment == "call":
        return RECONCILE_CALL
    parts = [RECONCILE_EPILOGUE]
    assertions = build_exec_assertions(executables)
    if assertions:
        parts.append(assertions)
    parts.append(RECONCILE_CALL)
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Doc-contract assertions (--doc-assertions)
# ---------------------------------------------------------------------------
#
# Parameterized, opt-in emissions for the per-project doc-contract rows
# of DOCS.md §9 and CODE.md §10 — the rows those tables label `contract`
# with enforcement "response's validation.sh". Bale stays
# project-agnostic: nothing here runs unconditionally; the worker pastes
# the emitted blocks into validation.sh beside the session-specific
# assertions (TARBALL.md §7.2 item 6), exactly like the §7.3 epilogue.
# The enforcement recipe those tables used to spell out in prose lives
# here now, where it cannot drift from what runs. Every block follows
# the same conventions as the exec-bit assertions: it prints
# [PASS]/[FAIL]/[SKIP] lines, assumes the enclosing script tracks
# failures in exit_code, and reads the manifest bale places at
# staging/.bale-manifest.json when it needs the change set — skipping
# loudly outside bale staging, never silently.

DOC_ASSERT_PREAMBLE = """\
# --- doc-contract assertions (crafted; DOCS.md 9 / CODE.md 10) ---
# Paste with your session-specific assertions (TARBALL.md 7.2 item 6).
# Assumes the enclosing script tracks failures in exit_code and exits
# with it. Blocks needing the change set read .bale-manifest.json and
# [SKIP] loudly when it is absent (not in bale staging).
"""

# DOCS.md §9: "INDEX.md lists every doc — a doc isn't real until INDEX
# lists it." Both directions: every doc this response ships under the
# INDEX's tree has an entry; every entry resolves to a file. Entries
# are the backticked paths of DOCS.md §2.3, resolved relative to the
# INDEX's own directory; the response's docs are the manifest's
# created/modified .md paths under that directory, excluding the INDEX
# itself and the responses/ and archive/ subtrees (session artifacts
# and archived docs are not main-body inventory — DOCS.md §1, §7.3).
DOC_ASSERT_INDEX_PY = """\
import json, re, sys
from pathlib import Path, PurePosixPath

index_rel = PurePosixPath(sys.argv[1]).as_posix()
index_path = Path(index_rel)
fails = []
if not index_path.is_file():
    print(f"[FAIL] INDEX coherence: {index_rel} not found in staging")
    raise SystemExit(1)
index_dir = PurePosixPath(index_rel).parent
text = index_path.read_bytes().decode("utf-8")
entries = re.findall(r"^\\s*-\\s*`([^`]+)`", text, flags=re.M)
resolved = {PurePosixPath(index_dir, e).as_posix() for e in entries}
dangling = sorted(e for e in entries
                  if not Path(PurePosixPath(index_dir, e)).exists())
if dangling:
    fails.append("INDEX entries not resolving to a file: "
                 + ", ".join(dangling))
else:
    print(f"[PASS] INDEX entries resolve ({len(entries)} entries)")
mpath = Path(".bale-manifest.json")
if not mpath.is_file():
    print("[SKIP] INDEX coverage of shipped docs: .bale-manifest.json "
          "not found (not in bale staging)")
else:
    changes = json.loads(mpath.read_bytes()).get("changes") or []
    tree = index_dir.as_posix()
    prefix = "" if tree == "." else tree + "/"
    exempt = tuple(prefix + sub + "/" for sub in ("responses", "archive"))
    shipped = sorted(
        c["path"] for c in changes
        if c.get("action") in ("created", "modified")
        and c["path"].endswith(".md")
        and c["path"].startswith(prefix)
        and c["path"] != index_rel
        and not c["path"].startswith(exempt))
    unindexed = [p for p in shipped if p not in resolved]
    if unindexed:
        fails.append("shipped docs with no INDEX entry: "
                     + ", ".join(unindexed))
    else:
        print(f"[PASS] shipped docs indexed ({len(shipped)} doc(s) "
              "under the INDEX tree)")
for msg in fails:
    print(f"[FAIL] INDEX coherence: {msg}")
raise SystemExit(1 if fails else 0)
"""

# DOCS.md §9's two ADR contract rows, one block: "ADRs are append-only
# — old ADRs are superseded, never rewritten" and "New ADR numbers are
# sequential and never reused". Mechanics:
# - a deleted entry under the ADR directory is a straight FAIL
#   (append-only; DOCS.md §7.2: ADRs are never prunable);
# - new ADR filenames match NNNN-lowercase-hyphenated.md and their
#   numbers continue max(existing)+1, consecutively;
# - a modified ADR must be confined to one of the two sanctioned diff
#   shapes (DOCS.md §5's status flow): the ratification flip (Status
#   Proposed -> Accepted, optionally plus a single appended dated
#   landing-note line) or the supersession flip (Status -> Superseded
#   plus populating Superseded by). Proven by reverse transform: undo
#   each sanctioned shape on the post-change bytes and require sha256
#   equality with the pre-change copy the request shipped — the hash
#   embedded at craft time from --adr-baseline. Any other diff fails:
#   no reconstruction reaches the pre-image.
DOC_ASSERT_ADR_PY = """\
import hashlib, json, re, sys
from pathlib import Path

adr_dir = sys.argv[1].rstrip("/")
baselines = dict(p.split("=", 1) for p in sys.argv[2:])
mpath = Path(".bale-manifest.json")
if not mpath.is_file():
    print("[SKIP] ADR guards: .bale-manifest.json not found "
          "(not in bale staging)")
    raise SystemExit(0)
changes = json.loads(mpath.read_bytes()).get("changes") or []
def under(p):
    return p.startswith(adr_dir + "/")
created = sorted(c["path"] for c in changes
                 if under(c["path"]) and c.get("action") == "created")
modified = sorted(c["path"] for c in changes
                  if under(c["path"]) and c.get("action") == "modified")
deleted = sorted(c["path"] for c in changes
                 if under(c["path"]) and c.get("action") == "deleted")
fails = []
if deleted:
    fails.append("ADRs are append-only; deleted: " + ", ".join(deleted))
name_re = re.compile(r"^(\\d{4})-[a-z0-9][a-z0-9-]*\\.md$")
created_names = {Path(p).name for p in created}
existing = []
d = Path(adr_dir)
if d.is_dir():
    for f in sorted(d.glob("*.md")):
        if f.name in created_names:
            continue
        m = name_re.match(f.name)
        if m:
            existing.append(int(m.group(1)))
new_nums = []
for p in created:
    m = name_re.match(Path(p).name)
    if not m:
        fails.append(f"new ADR {p} does not match "
                     "NNNN-lowercase-hyphenated.md")
    else:
        new_nums.append(int(m.group(1)))
if new_nums:
    base = max(existing, default=0)
    expect = list(range(base + 1, base + 1 + len(new_nums)))
    if sorted(new_nums) != expect:
        fails.append(f"new ADR numbers {sorted(new_nums)} != expected "
                     f"{expect} (max existing {base:04d})")
    else:
        print(f"[PASS] new ADR numbering sequential ({len(new_nums)} "
              f"new after {base:04d})")
else:
    print("[PASS] ADR numbering (no new ADRs)")
DATED = re.compile(r"^(?:[-*]\\s*)?\\d{4}-\\d{2}-\\d{2}[:\\s]")
def candidates(text):
    out = []
    if "- **Status:** Accepted" in text:
        rat = text.replace("- **Status:** Accepted",
                           "- **Status:** Proposed", 1)
        out.append(rat)
        lines = rat.splitlines(keepends=True)
        for i, ln in enumerate(lines):
            if DATED.match(ln.strip()):
                out.append("".join(lines[:i] + lines[i + 1:]))
    if "- **Status:** Superseded" in text:
        for pre in ("Accepted", "Proposed"):
            t = text.replace("- **Status:** Superseded",
                             f"- **Status:** {pre}", 1)
            t = re.sub(r"(?m)^- \\*\\*Superseded by:\\*\\* .+$",
                       "- **Superseded by:** \\u2014", t, count=1)
            out.append(t)
    return out
for p in modified:
    want = baselines.get(Path(p).name)
    if want is None:
        fails.append(f"modified ADR {p} has no embedded baseline hash "
                     "— re-emit --doc-assertions with --adr-baseline "
                     "pointing at the pre-change copies")
        continue
    f = Path(p)
    if not f.is_file():
        fails.append(f"modified ADR {p} missing from staging")
        continue
    post = f.read_bytes().decode("utf-8")
    got = {hashlib.sha256(c.encode("utf-8")).hexdigest()
           for c in candidates(post)}
    if want in got:
        print(f"[PASS] ADR modification confined to a sanctioned flip: {p}")
    else:
        fails.append(f"ADR modification is not a sanctioned flip "
                     f"(ratification or supersession): {p}")
if not modified and not deleted:
    print("[PASS] ADR append-only (no modified or deleted ADRs)")
for msg in fails:
    print(f"[FAIL] ADR guards: {msg}")
raise SystemExit(1 if fails else 0)
"""

# DOCS.md §9: "Pruning is always declared — every removal distinguishes
# archive from delete in its reason." Mechanics: every deleted entry's
# reason names one of the two §7.3 dispositions — a word on the
# archiv-/delet- stem. Non-empty reasons are already bale's contract
# (TARBALL.md §5.2); the pattern match is the doc-inventory residue.
DOC_ASSERT_PRUNE_PY = """\
import json, re, sys
from pathlib import Path

mpath = Path(".bale-manifest.json")
if not mpath.is_file():
    print("[SKIP] prune declarations: .bale-manifest.json not found "
          "(not in bale staging)")
    raise SystemExit(0)
changes = json.loads(mpath.read_bytes()).get("changes") or []
deleted = [c for c in changes if c.get("action") == "deleted"]
pat = re.compile(r"archiv|delet", re.I)
bad = sorted(c["path"] for c in deleted
             if not pat.search(c.get("reason") or ""))
if not deleted:
    print("[PASS] prune declarations (no deleted entries)")
elif bad:
    print("[FAIL] prune declarations: reasons naming neither archive "
          "nor delete: " + ", ".join(bad))
    raise SystemExit(1)
else:
    print(f"[PASS] prune declarations ({len(deleted)} delete(s) "
          "distinguish archive from delete)")
"""

# CODE.md §2.3/§10: "Index header lists every section — a section isn't
# navigable until listed." Both directions, per named file: every
# numbered banner (the §2.2 dash/name/dash comment shape) has a header
# entry (the `N. Name (~line M)` listing above the first banner), every
# header entry resolves to a banner, and names agree per number
# (whitespace-normalized; the approximate line numbers are §2.2's
# tolerated drift and are not checked).
DOC_ASSERT_HEADER_PY = """\
import re, sys
from pathlib import Path

DASH = re.compile(r"^\\s*#\\s*-{10,}\\s*$")
BANNER = re.compile(r"^\\s*#\\s*(\\d+)\\.\\s+(.+?)\\s*$")
ENTRY = re.compile(r"^\\s*#?\\s*(\\d+)\\.\\s+(.+?)\\s+\\(~?line\\s+\\d+\\)\\s*$")
def norm(s):
    return " ".join(s.split())
fails = []
for rel in sys.argv[1:]:
    f = Path(rel)
    if not f.is_file():
        fails.append(f"{rel}: not found in staging")
        continue
    lines = f.read_bytes().decode("utf-8").splitlines()
    banners = {}
    first_banner = None
    for i in range(len(lines) - 2):
        if DASH.match(lines[i]) and DASH.match(lines[i + 2]):
            m = BANNER.match(lines[i + 1])
            if m:
                if first_banner is None:
                    first_banner = i
                banners[int(m.group(1))] = norm(m.group(2))
    head = lines[:first_banner] if first_banner is not None else lines
    header = {}
    for ln in head:
        m = ENTRY.match(ln)
        if m:
            header[int(m.group(1))] = norm(m.group(2))
    if not banners and not header:
        fails.append(f"{rel}: no numbered banners and no index-header "
                     "listing found")
        continue
    problems = []
    for n in sorted(set(banners) - set(header)):
        problems.append(f"banner '{n}. {banners[n]}' missing from the "
                        "header")
    for n in sorted(set(header) - set(banners)):
        problems.append(f"header entry '{n}. {header[n]}' has no banner")
    for n in sorted(set(header) & set(banners)):
        if header[n] != banners[n]:
            problems.append(f"section {n} is {banners[n]!r} in the body "
                            f"but {header[n]!r} in the header")
    if problems:
        fails.append(f"{rel}: " + "; ".join(problems))
    else:
        print(f"[PASS] index header coherent: {rel} "
              f"({len(banners)} section(s))")
for msg in fails:
    print(f"[FAIL] index header: {msg}")
raise SystemExit(1 if fails else 0)
"""


def _doc_assert_block(banner: str, py_body: str, delim: str,
                      argv: list[str]) -> str:
    """One pasted block: banner comment, guarded python3 heredoc."""
    args = "".join(" " + shell_quote(a) for a in argv)
    return (f"{banner}"
            f"if ! python3 -{args} <<'{delim}'\n"
            f"{py_body}"
            f"{delim}\n"
            "then\n"
            "  exit_code=1\n"
            "fi\n")


def build_doc_assertions(index: str | None, adr_dir: str | None,
                         adr_baselines: dict[str, str], prune: bool,
                         index_headers: list[str]) -> str:
    """The full --doc-assertions emission, in table order: INDEX
    coherence, ADR guards, prune declarations, index-header coherence.
    Only the requested blocks emit; parameters ride as heredoc argv."""
    parts = [DOC_ASSERT_PREAMBLE]
    if index:
        parts.append(_doc_assert_block(
            "# --- INDEX coherence (crafted; DOCS.md 9, 2.3) ---\n",
            DOC_ASSERT_INDEX_PY, "BALE_DOC_INDEX", [index]))
    if adr_dir:
        pairs = [f"{name}={sha}"
                 for name, sha in sorted(adr_baselines.items())]
        parts.append(_doc_assert_block(
            "# --- ADR guards: append-only, sanctioned flips, sequential "
            "numbering (crafted; DOCS.md 5, 9) ---\n",
            DOC_ASSERT_ADR_PY, "BALE_DOC_ADR", [adr_dir, *pairs]))
    if prune:
        parts.append(_doc_assert_block(
            "# --- prune declarations (crafted; DOCS.md 7.3, 9) ---\n",
            DOC_ASSERT_PRUNE_PY, "BALE_DOC_PRUNE", []))
    if index_headers:
        parts.append(_doc_assert_block(
            "# --- index-header coherence (crafted; CODE.md 2.3, 10) ---\n",
            DOC_ASSERT_HEADER_PY, "BALE_DOC_HEADER", index_headers))
    return "\n".join(parts)


def shell_quote(path_str: str) -> str:
    """Quote a repo-relative path for the apply.sh scaffold. Plain paths
    stay bare (readable); anything shell-significant gets single-quoted."""
    safe = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
               "0123456789._-/+")
    if path_str and all(c in safe for c in path_str):
        return path_str
    return "'" + path_str.replace("'", "'\\''") + "'"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        prog="craft_response.py",
        description=("Scaffold a bale response (--kind normal | bailout | "
                     "clarification): the manifest skeleton, apply.sh, and "
                     "the non-normal kinds' companion artifacts. The "
                     "crafter never validates its own output; run "
                     "tools/response_lint.py on the finished response."),
    )
    ap.add_argument("response_dir", nargs="?", default=None,
                    help="the response-NNN/ directory (required except "
                         "under --probe, which reads no response dir)")
    ap.add_argument("--probe", default=None, metavar="SLUG",
                    help="emit the TARBALL.md 4.2 probe skeleton for SLUG "
                         "to stdout; mutually exclusive with the "
                         "response-directory modes and flags")
    ap.add_argument("--bundle", default=None, metavar="STEM",
                    help="assemble the planner bundle STEM + the reserved "
                         "suffix (board 49b, desk-side) and print the bale "
                         "open paste line; mutually exclusive with the "
                         "response-directory modes and flags, and with "
                         "--probe")
    ap.add_argument("--pack-arg", action="append", default=[],
                    metavar="TOKEN", dest="pack_arg",
                    help="with --bundle: one stored pack-argv token, "
                         "repeatable in order — the vector AFTER the pack "
                         "subcommand; never a delivery flag, never the "
                         "verb itself. Dash-leading tokens use the =-glued "
                         "spelling: --pack-arg=--slug")
    ap.add_argument("--brief", default=None, metavar="FILE",
                    help="with --bundle: the brief member's file (stored "
                         "flat as brief.md); exactly one of --brief / "
                         "--no-brief is required")
    ap.add_argument("--no-brief", action="store_true",
                    help="with --bundle: pack a deliberate no-brief bundle "
                         "(members.brief is an explicit null; the consumer "
                         "injects --no-readme from it)")
    ap.add_argument("--checkpoint", default=None, metavar="FILE",
                    help="with --bundle: the blind-checkpoint member's file "
                         "(stored flat as checkpoint.sh); absent means "
                         "members.checkpoint is an explicit null")
    ap.add_argument("--pre-answered", action="append", default=[],
                    metavar="PROMPT=SUBJECT", dest="pre_answered",
                    help="with --bundle: one pre-answered intent, "
                         "repeatable; PROMPT is from the closed vocabulary "
                         "(" + ", ".join(INTENT_PROMPTS) + "), SUBJECT is "
                         "what it answers about (for supersede, the parent "
                         "session id)")
    ap.add_argument("--out-dir", default=None, metavar="DIR",
                    help="with --bundle: directory the bundle file is "
                         "written into (default: the current directory)")
    ap.add_argument("--emit-block", default=None, metavar="FILE",
                    dest="emit_block",
                    help="render the counterpart-facing exchange paste "
                         "block for FILE (a filled clarification manifest "
                         "or a filled worker exchange record; `-` reads "
                         "stdin) to stdout, byte-identical to what `bale "
                         "relay` emits for the same record; mutually "
                         "exclusive with the response-directory modes and "
                         "flags, and with --probe and --bundle")
    ap.add_argument("--round", type=int, default=None, metavar="N",
                    help="with --emit-block: the round the record occupies "
                         "(integer >= 1, default 1). On a clarification "
                         "manifest it fills the normalized record's round; "
                         "on an exchange record it asserts the record's "
                         "own round, and a contradiction refuses rather "
                         "than rewrites")
    ap.add_argument("--sid", default=None,
                    help="session id (fills session_id and responds_to)")
    ap.add_argument("--kind", choices=KINDS, default=None,
                    help="response kind to scaffold (default: normal)")
    ap.add_argument("--questions", type=int, default=None, metavar="N",
                    help="with --kind clarification: number of "
                         "question-entry stubs to seed (default 1)")
    ap.add_argument("--deleted", action="append", default=[], metavar="PATH",
                    help="emit a deleted-entry stub for PATH (repeatable)")
    ap.add_argument("--executable", action="append", default=[],
                    metavar="PATH",
                    help="emit a chmod +x line in apply.sh for PATH "
                         "(repeatable; PATH must be under files/)")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--changes-only", action="store_true",
                      help="print only the changes[] array")
    mode.add_argument("--apply-only", action="store_true",
                      help="print only the apply.sh scaffold")
    mode.add_argument("--write", action="store_true",
                      help="write manifest.json and apply.sh into the "
                           "response dir")
    mode.add_argument("--validation-epilogue", action="store_true",
                      help="print the paste-ready validation.sh fragments: "
                           "the TARBALL.md 7.3 reconciliation epilogue plus "
                           "a 7.7 exec-bit assertion per --executable path")
    mode.add_argument("--doc-assertions", action="store_true",
                      help="print paste-ready validation.sh blocks for the "
                           "per-project doc-contract rows of DOCS.md 9 / "
                           "CODE.md 10; select blocks with --index, "
                           "--adr-dir, --prune-reasons, --index-header")
    ap.add_argument("--fragment", choices=("definitions", "assertions",
                                           "call"), default=None,
                    help="with --validation-epilogue: emit exactly one "
                         "separable part instead of the combined block — "
                         "definitions (paste before the checks), assertions "
                         "(paste with the session-specific assertions; "
                         "needs --executable), or call (paste last)")
    ap.add_argument("--index", default=None, metavar="PATH",
                    help="with --doc-assertions: repo-relative path of the "
                         "project's INDEX.md; emits the DOCS.md 9 "
                         "INDEX-coherence block")
    ap.add_argument("--adr-dir", default=None, metavar="PATH",
                    help="with --doc-assertions: repo-relative ADR "
                         "directory; emits the DOCS.md 9 ADR guards "
                         "(append-only, sanctioned flips, sequential "
                         "numbering)")
    ap.add_argument("--adr-baseline", default=None, metavar="DIR",
                    help="with --doc-assertions --adr-dir: local directory "
                         "holding the pre-change ADR copies (typically the "
                         "request's context/ copy); pre-change sha256s for "
                         "the reverse-transform are computed from it at "
                         "craft time")
    ap.add_argument("--prune-reasons", action="store_true",
                    help="with --doc-assertions: emit the DOCS.md 9 "
                         "prune-declaration block (deleted entries' reasons "
                         "distinguish archive from delete)")
    ap.add_argument("--index-header", action="append", default=[],
                    metavar="PATH",
                    help="with --doc-assertions: repo-relative file carrying "
                         "a CODE.md 2.2 index header; emits the CODE.md 10 "
                         "header-coherence block (repeatable)")
    ap.add_argument("--force", action="store_true",
                    help="with --write: overwrite existing manifest.json / "
                         "apply.sh; with --bundle: overwrite an existing "
                         "bundle whose bytes differ (an identical re-run "
                         "is an idempotent no-op without it)")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    # Probe mode. A probe is a chat paste-back, not a response-directory
    # artifact (TARBALL.md §4.2): it reads no response dir and combines
    # with none of the response-directory modes or flags, so every such
    # combination is a flag error, not a silent ignore.
    if args.probe is not None:
        supplied = [flag for flag, given in (
            ("--kind", args.kind is not None),
            ("--changes-only", args.changes_only),
            ("--apply-only", args.apply_only),
            ("--write", args.write),
            ("--validation-epilogue", args.validation_epilogue),
            ("--doc-assertions", args.doc_assertions),
            ("--fragment", args.fragment is not None),
            ("--index", args.index is not None),
            ("--adr-dir", args.adr_dir is not None),
            ("--adr-baseline", args.adr_baseline is not None),
            ("--prune-reasons", args.prune_reasons),
            ("--index-header", bool(args.index_header)),
            ("--sid", args.sid is not None),
            ("--questions", args.questions is not None),
            ("--deleted", bool(args.deleted)),
            ("--executable", bool(args.executable)),
            ("--force", args.force),
            ("--bundle", args.bundle is not None),
            ("--pack-arg", bool(args.pack_arg)),
            ("--brief", args.brief is not None),
            ("--no-brief", args.no_brief),
            ("--checkpoint", args.checkpoint is not None),
            ("--pre-answered", bool(args.pre_answered)),
            ("--out-dir", args.out_dir is not None),
            ("--emit-block", args.emit_block is not None),
            ("--round", args.round is not None),
        ) if given]
        if supplied:
            return die(f"--probe is mutually exclusive with "
                       f"{', '.join(supplied)} — a probe is a chat "
                       "paste-back, not a response-directory artifact "
                       "(TARBALL.md 4.2)")
        if args.response_dir is not None:
            return die(f"--probe takes no response dir (got "
                       f"{args.response_dir!r}) — the skeleton goes to "
                       "stdout and a probe produces no artifact directory "
                       "(TARBALL.md 4.2); drop the positional argument")
        problem = slug_problem(args.probe)
        if problem:
            return die(f"--probe: {problem}")
        clip, note = read_clipboard_command()
        sys.stdout.write(build_probe_scaffold(args.probe, clip))
        if clip is not None:
            log(f"clipboard epilogue emitted ({note}) — the scaffold "
                "tees its sentinel-bracketed output to the configured "
                "command at run time, loudly either way")
        else:
            log(f"clipboard epilogue not emitted ({note}) — remedy "
                "text in the scaffold walks the operator through the "
                "[probe] clipboard_command opt-in")
        log("probe skeleton emitted — fill the TODO placeholders (what, "
            "why, real sections with caps), then paste into chat; no lint "
            "runs on a probe — the architect audits it by eye "
            "(TARBALL.md 4.2)")
        return EXIT_OK

    # Bundle mode (board 49b). Desk-side emission of a planner bundle:
    # like --probe, it reads no response dir and combines with none of
    # the response-directory modes or flags, so every such combination
    # is a flag error, not a silent ignore. The emitter assembles —
    # hashes computed from the LF-normalized bytes it writes, delivery
    # flags never stored — and never executes anything: the dry-run
    # proof and the authoritative manifest gate are `bale open`'s.
    if args.bundle is not None:
        supplied = [flag for flag, given in (
            ("--kind", args.kind is not None),
            ("--changes-only", args.changes_only),
            ("--apply-only", args.apply_only),
            ("--write", args.write),
            ("--validation-epilogue", args.validation_epilogue),
            ("--doc-assertions", args.doc_assertions),
            ("--fragment", args.fragment is not None),
            ("--index", args.index is not None),
            ("--adr-dir", args.adr_dir is not None),
            ("--adr-baseline", args.adr_baseline is not None),
            ("--prune-reasons", args.prune_reasons),
            ("--index-header", bool(args.index_header)),
            ("--sid", args.sid is not None),
            ("--questions", args.questions is not None),
            ("--deleted", bool(args.deleted)),
            ("--executable", bool(args.executable)),
            ("--emit-block", args.emit_block is not None),
            ("--round", args.round is not None),
        ) if given]
        if supplied:
            return die(f"--bundle is mutually exclusive with "
                       f"{', '.join(supplied)} — a planner bundle is a "
                       "desk-side artifact, not a response-directory one "
                       "(board 49b)")
        if args.response_dir is not None:
            return die(f"--bundle takes no response dir (got "
                       f"{args.response_dir!r}) — the bundle lands under "
                       "--out-dir and the paste line goes to stdout; drop "
                       "the positional argument")
        problem = bundle_stem_problem(args.bundle)
        if problem:
            return die(f"--bundle: {problem}")
        if args.brief is not None and args.no_brief:
            return die("--brief and --no-brief contradict — a bundle "
                       "either ships the brief member or declares the "
                       "explicit null, never both")
        if args.brief is None and not args.no_brief:
            return die("one of --brief / --no-brief is required — a "
                       "no-brief bundle is a deliberate acknowledgment "
                       "(the --no-readme precedent), never a default")
        if not args.pack_arg:
            return die("--bundle needs at least one --pack-arg token — "
                       "pack_argv is required non-empty (the vector "
                       "AFTER the pack subcommand)")
        for i, token in enumerate(args.pack_arg):
            problem = pack_arg_problem(token, i)
            if problem:
                return die(problem)
        intents: list[tuple[str, str]] = []
        for spec in args.pre_answered:
            parsed = parse_intent(spec)
            if isinstance(parsed, str):
                return die(parsed)
            if parsed in intents:
                return die(f"--pre-answered duplicates "
                           f"{parsed[0]}={parsed[1]} — one intent per "
                           "prompt-and-subject; the consumer refuses "
                           "duplicates at parse")
            intents.append(parsed)

        brief_bytes: bytes | None = None
        if args.brief is not None:
            got = read_bundle_input("--brief", args.brief)
            if isinstance(got, str):
                return die(got)
            brief_bytes = normalize_member(got)
            offenders = [n for n, ln in enumerate(
                brief_bytes.decode("utf-8", errors="replace")
                .splitlines(), 1) if BRIEF_PLACEHOLDER in ln]
            if offenders:
                return die(f"--brief: {args.brief} still contains the "
                           f"unfilled placeholder sentinel "
                           f"'{BRIEF_PLACEHOLDER}' on line(s) "
                           f"{', '.join(map(str, offenders))} — the "
                           "replayed pack would refuse it at the "
                           "operator's open (TARBALL.md 3.4); fill or "
                           "remove every such line at the desk instead")
        checkpoint_bytes: bytes | None = None
        if args.checkpoint is not None:
            got = read_bundle_input("--checkpoint", args.checkpoint)
            if isinstance(got, str):
                return die(got)
            checkpoint_bytes = normalize_member(got)

        manifest = build_bundle_manifest(
            args.pack_arg, brief_bytes, checkpoint_bytes, intents)
        members: dict[str, bytes] = {}
        if brief_bytes is not None:
            members[BRIEF_MEMBER] = brief_bytes
        if checkpoint_bytes is not None:
            members[CHECKPOINT_MEMBER] = checkpoint_bytes
        blob = bundle_archive_bytes(manifest, members)

        out_dir = Path(args.out_dir) if args.out_dir is not None \
            else Path.cwd()
        if not out_dir.is_dir():
            return die(f"--out-dir: not a directory: {out_dir}")
        filename = args.bundle + BUNDLE_SUFFIX
        out_path = out_dir / filename
        if out_path.exists():
            if out_path.is_file() and out_path.read_bytes() == blob:
                log(f"{out_path} already exists with identical bytes — "
                    "idempotent re-run, nothing written")
                print(f"bale open {filename}")
                return EXIT_OK
            if not args.force:
                return die(f"{out_path} exists with different content — "
                           "re-run with --force to overwrite")
        out_path.write_bytes(blob)

        for slot in ("brief", "checkpoint"):
            entry = manifest["members"][slot]
            if entry is None:
                log(f"member {slot}: explicit null (not shipped)")
            else:
                log(f"member {slot}: {entry['path']} "
                    f"(sha256 {entry['sha256'][:12]}…, LF-normalized "
                    f"bytes as written)")
        log(f"pack_argv: {len(args.pack_arg)} token(s); pre_answered: "
            f"{len(intents)} intent(s)")
        if checkpoint_bytes is None:
            log("no checkpoint member — the bundle is oracle-less; a "
                "checkpoint-configured project's replayed pack will "
                "refuse it")
        log(f"wrote {out_path} ({len(blob)} bytes) — ship the file and "
            "the printed line together; the line carries the bundle "
            "filename only, so a downloads-dir save is paste-ready")
        print(f"bale open {filename}")
        return EXIT_OK

    # Exchange-block mode (TARBALL.md §5.9.2, the worker-side flow). Like
    # --probe and --bundle it reads no response dir and combines with none
    # of the response-directory modes or flags — every such combination is
    # a flag error, not a silent ignore. stdout is the block and only the
    # block (relay's stream discipline, so `--emit-block r.json > block.txt`
    # captures it clean); every [craft] line is already stderr's.
    if args.emit_block is not None:
        supplied = [flag for flag, given in (
            ("--kind", args.kind is not None),
            ("--changes-only", args.changes_only),
            ("--apply-only", args.apply_only),
            ("--write", args.write),
            ("--validation-epilogue", args.validation_epilogue),
            ("--doc-assertions", args.doc_assertions),
            ("--fragment", args.fragment is not None),
            ("--index", args.index is not None),
            ("--adr-dir", args.adr_dir is not None),
            ("--adr-baseline", args.adr_baseline is not None),
            ("--prune-reasons", args.prune_reasons),
            ("--index-header", bool(args.index_header)),
            ("--sid", args.sid is not None),
            ("--questions", args.questions is not None),
            ("--deleted", bool(args.deleted)),
            ("--executable", bool(args.executable)),
            ("--force", args.force),
            ("--pack-arg", bool(args.pack_arg)),
            ("--brief", args.brief is not None),
            ("--no-brief", args.no_brief),
            ("--checkpoint", args.checkpoint is not None),
            ("--pre-answered", bool(args.pre_answered)),
            ("--out-dir", args.out_dir is not None),
        ) if given]
        if supplied:
            return die(f"--emit-block is mutually exclusive with "
                       f"{', '.join(supplied)} — the block is a paste "
                       "carried to the planner, not a response-directory "
                       "artifact (TARBALL.md 5.9.2)")
        if args.response_dir is not None:
            return die(f"--emit-block takes no response dir (got "
                       f"{args.response_dir!r}) — it renders the record in "
                       "the named file to stdout; drop the positional "
                       "argument")
        if args.round is not None and args.round < 1:
            return die(f"--round must be at least 1 — a thread's rounds are "
                       f"the NNN files under .bale/clarifications/<sid>/ and "
                       f"they start at 1 (got {args.round})")
        got = read_emit_block_input(args.emit_block)
        if isinstance(got, str):
            return die(got)
        try:
            block, what = build_emit_block(got, args.round)
        except ValueError as exc:
            return die(str(exc))
        sys.stdout.write(block)
        log(what)
        log("block emitted on stdout — hand it to the courier for `bale "
            "relay <sid> <file|->`; the trailer is the sha256 of the body "
            "bytes, so a truncated paste refuses on ingest instead of "
            "being reasoned from (TARBALL.md 5.9.2)")
        return EXIT_OK

    stray_bundle = [flag for flag, given in (
        ("--pack-arg", bool(args.pack_arg)),
        ("--brief", args.brief is not None),
        ("--no-brief", args.no_brief),
        ("--checkpoint", args.checkpoint is not None),
        ("--pre-answered", bool(args.pre_answered)),
        ("--out-dir", args.out_dir is not None),
    ) if given]
    if stray_bundle:
        return die(f"{', '.join(stray_bundle)}: only meaningful with "
                   "--bundle")

    if args.round is not None:
        return die("--round: only meaningful with --emit-block")

    if args.response_dir is None:
        return die("response dir is required (only --probe and --bundle "
                   "run without one)")
    rdir = Path(args.response_dir)
    if not rdir.is_dir():
        return die(f"response dir not found or not a directory: {rdir}")
    if args.force and not args.write:
        return die("--force only means something with --write or "
                   "--bundle")

    kind = args.kind if args.kind is not None else "normal"

    # Kind/flag coherence. This is argument hygiene, not response
    # validation (the judge stays tools/response_lint.py): each of these
    # combinations would scaffold an artifact the contract forbids, so
    # the tool refuses to scaffold it rather than judging it later.
    if kind != "normal":
        if args.deleted or args.executable:
            return die(f"--deleted/--executable are meaningless with "
                       f"--kind {kind} — a {kind} response has empty "
                       "change surfaces (TARBALL.md 5.6.2 / 5.9.2)")
        if args.changes_only:
            return die(f"--changes-only is meaningless with --kind {kind} "
                       f"— a {kind} response has an empty changes[] "
                       "(TARBALL.md 5.6.2 / 5.9.2)")
        if args.validation_epilogue:
            return die(f"--validation-epilogue is meaningless with --kind "
                       f"{kind} — a {kind} response's validation.sh is the "
                       "contract-fixed no-op (TARBALL.md 5.6.1 / 5.9.2)")
        if args.doc_assertions:
            return die(f"--doc-assertions is meaningless with --kind "
                       f"{kind} — a {kind} response's validation.sh is the "
                       "contract-fixed no-op (TARBALL.md 5.6.1 / 5.9.2)")
    if args.questions is not None:
        if kind != "clarification":
            return die("--questions only means something with "
                       "--kind clarification")
        if args.questions < 1:
            return die("--questions must be at least 1 — questions[] is "
                       "required non-empty on a clarification "
                       "(TARBALL.md 5.9.2)")
    n_questions = args.questions if args.questions is not None else 1

    if args.fragment is not None and not args.validation_epilogue:
        return die("--fragment only means something with "
                   "--validation-epilogue")
    if args.fragment == "assertions" and not args.executable:
        return die("--fragment assertions has nothing to emit without "
                   "--executable paths — the exec-bit assertions are "
                   "generated from that list (TARBALL.md 7.7)")

    doc_selectors = (("--index", args.index is not None),
                     ("--adr-dir", args.adr_dir is not None),
                     ("--prune-reasons", args.prune_reasons),
                     ("--index-header", bool(args.index_header)))
    if not args.doc_assertions:
        stray = [flag for flag, given in
                 (*doc_selectors, ("--adr-baseline",
                                   args.adr_baseline is not None)) if given]
        if stray:
            return die(f"{', '.join(stray)}: only meaningful with "
                       "--doc-assertions")
    else:
        if not any(given for _, given in doc_selectors):
            return die("--doc-assertions needs at least one block selected "
                       "— --index, --adr-dir, --prune-reasons, or "
                       "--index-header")
        if args.deleted or args.executable:
            return die("--deleted/--executable are meaningless with "
                       "--doc-assertions — the emission is a validation.sh "
                       "fragment, not a change-set scaffold")
        if args.adr_baseline is not None and args.adr_dir is None:
            return die("--adr-baseline only means something with --adr-dir")
        for label, value in (("--index", args.index),
                             ("--adr-dir", args.adr_dir)):
            if value is not None:
                problem = rel_path_problem(value)
                if problem:
                    return die(f"{label}: {problem}")
        seen: set[str] = set()
        for v in args.index_header:
            problem = rel_path_problem(v)
            if problem:
                return die(f"--index-header: {problem}")
            if v in seen:
                return die(f"--index-header: duplicate path {v!r}")
            seen.add(v)

    needs_sid = not (args.changes_only or args.apply_only
                     or args.validation_epilogue or args.doc_assertions)
    sid = (args.sid or "").strip()
    if needs_sid and not sid:
        return die("--sid is required when emitting a manifest (only "
                   "--changes-only / --apply-only / --validation-epilogue "
                   "run without it)")

    # Worker-supplied path sanity. This is argument hygiene, not response
    # validation: a typo'd flag scaffolding a wrong rm/chmod line is the
    # failure it prevents. Judging the finished response stays the lint's.
    for label, values in (("--deleted", args.deleted),
                          ("--executable", args.executable)):
        seen: set[str] = set()
        for v in values:
            problem = rel_path_problem(v)
            if problem:
                return die(f"{label}: {problem}")
            if v in seen:
                return die(f"{label}: duplicate path {v!r}")
            seen.add(v)

    files_root = rdir / "files"
    try:
        mirror = set(walk_mirror(files_root)) if files_root.is_dir() else set()
    except ValueError as exc:
        return die(str(exc))

    if kind != "normal" and mirror:
        return die(f"files/ holds {len(mirror)} file(s) but a {kind} "
                   "response ships no file changes (TARBALL.md 5.6.1 / "
                   "5.9.2) — clear files/ or craft in a clean response dir")

    for v in args.deleted:
        if v in mirror:
            return die(f"--deleted {v!r} also exists under files/ — a "
                       "deleted entry carries no mirror file (TARBALL.md "
                       "5.2); remove one or the other")
    for v in args.executable:
        if v not in mirror:
            return die(f"--executable {v!r} has no file under files/ — a "
                       "chmod line for an unshipped path restores nothing")

    try:
        changes = build_changes(files_root if files_root.is_dir() else None,
                                args.deleted)
    except ValueError as exc:
        return die(str(exc))
    apply_sh = (APPLY_NOOP if kind != "normal"
                else build_apply_sh(args.deleted, args.executable))

    if kind == "normal":
        log(f"files/ mirror: {len(mirror)} file(s); deleted stubs: "
            f"{len(args.deleted)}; chmod lines: {len(args.executable)}")
    else:
        log(f"scaffolding a {kind} response — empty change surfaces, "
            "no-op apply.sh and validation.sh")

    if args.doc_assertions:
        adr_baselines: dict[str, str] = {}
        if args.adr_dir is not None:
            adr_prefix = args.adr_dir.rstrip("/") + "/"
            adr_mirror = sorted(p for p in mirror
                                if p.startswith(adr_prefix))
            if args.adr_baseline is not None:
                bdir = Path(args.adr_baseline)
                if not bdir.is_dir():
                    return die(f"--adr-baseline: not a directory: {bdir}")
                for rel in adr_mirror:
                    src = bdir / Path(rel).name
                    if src.is_file():
                        adr_baselines[Path(rel).name] = sha256_of(src)
                log(f"ADR baselines: {len(adr_baselines)} pre-change "
                    f"hash(es) embedded from {bdir} ({len(adr_mirror)} "
                    "ADR file(s) in the mirror)")
            elif adr_mirror:
                log(f"warning: {len(adr_mirror)} file(s) under "
                    f"files/{adr_prefix} and no --adr-baseline — all "
                    "treated as created; a modified ADR will FAIL at "
                    "validation without its embedded pre-change hash")
        sys.stdout.write(build_doc_assertions(
            args.index, args.adr_dir, adr_baselines, args.prune_reasons,
            args.index_header))
        log("doc-contract assertion blocks emitted — paste with your "
            "session-specific assertions (TARBALL.md 7.2 item 6); the "
            "blocks assume the enclosing script tracks failures in "
            "exit_code")
        return EXIT_OK

    if args.validation_epilogue:
        sys.stdout.write(build_validation_epilogue(args.executable,
                                                   args.fragment))
        if args.fragment is None:
            log("validation.sh fragments emitted — paste the definitions "
                "before your checks, the exec-bit assertions (if any) with "
                "your session-specific assertions, and the reconcile_claims "
                "call last; which checks run stays your judgment "
                "(TARBALL.md 7.2)")
        else:
            placement = {
                "definitions": "before your checks",
                "assertions": "with your session-specific assertions",
                "call": "last, after every check has recorded its verdict",
            }[args.fragment]
            log(f"validation.sh fragment emitted ({args.fragment}) — "
                f"paste it {placement}; which checks run stays your "
                "judgment (TARBALL.md 7.2)")
        return EXIT_OK

    if args.changes_only:
        print(json.dumps(changes, indent=2))
        log("changes[] skeleton emitted — fill action and reason per entry, "
            "then run tools/response_lint.py on the finished response")
        return EXIT_OK

    if args.apply_only:
        sys.stdout.write(apply_sh)
        log("apply.sh scaffold emitted")
        return EXIT_OK

    manifest = build_manifest(sid, kind, changes, n_questions)

    # The kind's artifact set for --write. The normal kind never gets a
    # validation.sh from this tool (worker's hypothesis test, §7); the
    # two non-normal kinds get the contract-fixed no-op, and a bailout
    # additionally gets its two required companions (§5.6.1).
    emit: list[tuple[str, str]] = [
        ("manifest.json", json.dumps(manifest, indent=2) + "\n"),
        ("apply.sh", apply_sh),
    ]
    if kind in VALIDATION_NOOP_BY_KIND:
        emit.append(("validation.sh", VALIDATION_NOOP_BY_KIND[kind]))
    if kind == "bailout":
        emit.append(("handoff.md", HANDOFF_SCAFFOLD))
        emit.append(("diagnostics.json",
                     json.dumps(build_diagnostics(sid), indent=2) + "\n"))

    if args.write:
        for name, _ in emit:
            dst = rdir / name
            if dst.exists() and not args.force:
                return die(f"{dst} exists — re-run with --force to "
                           "overwrite")
        wrote: list[Path] = []
        for name, body in emit:
            dst = rdir / name
            dst.write_text(body, encoding="utf-8")
            wrote.append(dst)
        for dst in wrote:
            print(dst)
        names = ", ".join(name for name, _ in emit)
        fill = {
            "normal": "fill summary, action, reason, validation_will_run, "
                      "and claims",
            "bailout": "fill summary, the handoff.md sections, and the "
                       "diagnostics.json fields (bail_trigger, "
                       "bail_narrative, ...)",
            "clarification": "fill summary and all four fields of every "
                             "questions[] entry",
        }[kind]
        log(f"wrote {names} — {fill}, then run tools/response_lint.py")
        return EXIT_OK

    print(json.dumps(manifest, indent=2))
    if kind == "normal":
        log("manifest skeleton emitted (apply.sh scaffold via --apply-only "
            "or --write) — fill the judgment fields, then run "
            "tools/response_lint.py")
    else:
        rest = ", ".join(name for name, _ in emit[1:])
        log(f"manifest skeleton emitted — the {kind} kind's remaining "
            f"artifacts ({rest}) are written by --write; fill the "
            "judgment fields, then run tools/response_lint.py")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
