#!/usr/bin/env bash
# Blind checkpoint — session twine-surface-row (bale-src), version 1.
# Authored 2026-10-13 by sitting 2026-10-13-twine-obligations-desk-001,
# from the request, before any implementation existed.
#
# Outcome contract only: what must be true of the applied tree. The
# cwd is the staged tree. Exit 0 = every probe passed; 1 = at least one
# probe failed (a HOLD on the work); 2 = this oracle is defective (a
# control failed or an unplanned exception) — never a verdict on the work.
# Verdict lines carry the label alone; detail follows on "  detail:" lines.
# Reads only; writes nothing; needs no sid, no manifest, no own path.
set -u
exec python3 -I -B - <<'ORACLE'
import hashlib, re, sys
from pathlib import Path

# ---------------------------------------------------------------- pins
AGENT = Path("docs/AGENT.md")
TARBALL = Path("docs/TARBALL.md")
UNTOUCHED = {
    "docs/DOCS.md":    "90cc9aad0670610b7865a54db33975103580cdd3354d000b8db07f8a6e956d0c",
    "docs/CODE.md":    "49a145323bfc472a22dd8be56565d6e7767fd1ffbd33c36cda95e7e3e149ab75",
    "docs/PLANNER.md": "22c4f52e73fde726b3ffab8256e2a957a18378093757f8882331315bbb2af82c",
}
# sha256 over the LF-joined list of heading lines ("#"-prefixed, then a
# space) as the request carried them — no heading added, renamed, removed.
HEADINGS = {
    "docs/AGENT.md":   "874ae6a539c8c738a08e8cbbe6038d0d9dc48f69c219a3f6e957f4290454c330",
    "docs/TARBALL.md": "c5478cce1ac31fa4c952b4226834fe1e3a73e7e0d4c083fa0477cd9051fd7ae8",
}
TWINE_CELLS = [
    "| `twine run` (a twine-hosted API worker: twine opens the session with `bale open`, hosts the worker in a sandbox home, hands it the request unpacked at `request/` and seven tools, and speaks to the model through an API adapter; the opener bale prints is the first user turn, verbatim) |",
    "| Nothing compacts: the conversation is append-only and every call sends it whole, so §11.6's recovery path never engages — there is no summary to recover from. The provider's own context-window error ends the run stopped, a stop whose move is the planner's split; a stopped run is resumed from its transcript or respawned from the request, as twine's contract says. Until twine's window accounting warns the worker as a tool result, no warning reaches it before the edge, so §11.3's bail-early discipline is the whole defense here |",
    "| There is no per-turn tool-use limit: every tool call a turn asks for runs, in order, and the results return as the next user turn. The bounds are twine's own — a model-call ceiling (`--max-turns`), a per-call `max_tokens` that keeps the partial turn and asks the model to continue, and a spend cap checked before each call. A light question block ends the run suspended, and the planner's answer is the next user turn when it resumes |",
    "| Not shown: the system prompt and the surface note name neither the model nor the provider, so `model_identity` is `unknown:unknown` — the vendor token too, since the surface withholds it. The exact string lives in twine's own records and reaches bale's record only mechanically, through `attempts[].cost` |",
]
PICKER_NEW = "Shown by the model picker, and on some sessions by the system prompt's model line; reported in `<vendor>:<model>` form — the API model string's spelling when the session sees one (`claude-opus-5-5`, not the picker's `claude-opus-5.5`), otherwise the picker's name lowercased with spaces as hyphens — and `unknown` when neither is visible to the session"
PICKER_OLD = "Shown by the model picker; reported verbatim in `<vendor>:<model>` form, `unknown` when the picker is not visible to the session"
LEAD_CLAUSE = "one that does not gets `unknown` as the model token, and as the vendor token too when the surface withholds the provider."
T522 = "with `unknown` as the model token when the surface does not show the string, and as the vendor token too when the surface withholds the provider (`AGENT.md` §11.7's table says which do)"
T71 = "**The scripts run in a PID namespace.** Under the sandbox, `validation.sh` and the checkpoint each run in a PID namespace of their own: the runner can be pid 1, and a process's inherited process-group id reads as 0 there. A script that registers *itself* by process group — to reap what it started, say — makes itself a session leader first (`os.setsid()`), or registers a child spawned for the purpose. `unshare -rpf --mount-proc` reproduces the namespace for a rehearsal."
T71_ANCHOR_BEFORE = "The script prints, at the top of its output, every location it will write to."
T71_ANCHOR_AFTER = "**A tree walk excludes the validation base path.**"

# ----------------------------------------------------------- detectors
def fold(s: str) -> str:
    return " ".join(s.split())

def contains(text: str, phrase: str) -> bool:
    return fold(phrase) in fold(text)

def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def heading_hash(text: str) -> str:
    hs = [l for l in text.split("\n")
          if l.startswith("#") and l.lstrip("#").startswith(" ")]
    return hashlib.sha256("\n".join(hs).encode("utf-8")).hexdigest()

def table_rows(text: str) -> list:
    """Data rows of the last markdown table in `text` (the §11.7 table):
    the lines after its '|---' separator that start with '| '."""
    lines = text.split("\n")
    seps = [i for i, l in enumerate(lines) if re.match(r"^\|\s*-{3,}", l)]
    if not seps:
        return []
    rows = []
    for l in lines[seps[-1] + 1:]:
        if l.startswith("| "):
            rows.append(l)
        elif l.strip():
            break
    return rows

def row_with_cells(rows: list, cells: list):
    for r in rows:
        if all(contains(r, c) for c in cells):
            return r
    return None

def between(text: str, before: str, after: str, phrase: str) -> bool:
    t = fold(text); i = t.find(fold(before)); j = t.find(fold(after))
    if i < 0 or j < 0 or j < i:
        return False
    return fold(phrase) in t[i:j]

# ------------------------------------------------------------- controls
# Each control calls the detector it guards; a control that fails means
# the oracle is broken, and the script exits 2 before any probe runs.
def control(name: str, ok: bool) -> None:
    if not ok:
        print(f"oracle control failed: {name}", file=sys.stderr)
        sys.exit(2)

def run_controls() -> None:
    control("fold", fold("a \n\t b  c") == "a b c")
    control("contains-positive", contains("x  y\nz", "y z"))
    control("contains-negative", not contains("x y z", "y q"))
    control("sha256", hashlib.sha256(b"").hexdigest().startswith("e3b0c442"))
    control("heading_hash-sensitive",
            heading_hash("# a\n## b\n") != heading_hash("# a\n## c\n"))
    control("heading_hash-fence-blind",
            heading_hash("# a\n#!/bin/sh\n") == heading_hash("# a\n"))
    sample = "| H | I |\n|---|---|\n| r1 | x |\n| r2 | y |\n\ntext"
    control("table_rows", table_rows(sample) == ["| r1 | x |", "| r2 | y |"])
    control("row_with_cells-positive",
            row_with_cells(table_rows(sample), ["| r2 |", "| y |"]) is not None)
    control("row_with_cells-negative",
            row_with_cells(table_rows(sample), ["| r2 |", "| x |"]) is None)
    control("between-positive", between("A p B", "A", "B", "p"))
    control("between-negative", not between("p A B", "A", "B", "p"))

# --------------------------------------------------------------- probes
failures = []
def probe(label: str, ok: bool, detail: str = "") -> None:
    print(f"[{'PASS' if ok else 'FAIL'}] {label}")
    if detail and not ok:
        print(f"  detail: {detail}")
    if not ok:
        failures.append(label)

def main() -> int:
    run_controls()
    agent = AGENT.read_text(encoding="utf-8")
    tarball = TARBALL.read_text(encoding="utf-8")

    rows = table_rows(agent)
    probe("agent-11.7-two-rows", len(rows) == 2,
          f"{len(rows)} data rows in the last table; 2 expected")
    probe("agent-11.7-twine-row",
          row_with_cells(rows, TWINE_CELLS) is not None,
          "no row carries all four pinned cells (whitespace folded)")
    probe("agent-11.7-picker-ruling", contains(agent, PICKER_NEW),
          "the ruled claude.ai model-string cell is absent")
    probe("agent-11.7-old-wording-gone", not contains(agent, PICKER_OLD),
          "the pre-ruling claude.ai cell text survives")
    probe("agent-11.7-vendor-token", contains(agent, LEAD_CLAUSE),
          "the lead paragraph's vendor-token clause is absent")
    probe("tarball-5.2.2-vendor-token", contains(tarball, T522),
          "§5.2.2's vendor-token passage is absent")
    probe("tarball-7.1-pid-namespace",
          between(tarball, T71_ANCHOR_BEFORE, T71_ANCHOR_AFTER, T71),
          "the PID-namespace paragraph is absent between its anchors")
    for rel, want in UNTOUCHED.items():
        got = sha256_of(Path(rel))
        probe(f"untouched-{Path(rel).name}", got == want,
              f"sha256 {got[:12]}… differs from the request's {want[:12]}…")
    for rel, want in HEADINGS.items():
        got = heading_hash(Path(rel).read_text(encoding="utf-8"))
        probe(f"headings-stable-{Path(rel).name}", got == want,
              "the heading list changed (added, renamed or removed)")

    if failures:
        print(f"HOLD: {len(failures)} probe(s) failed")
        return 1
    print("PASS: every probe passed")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except BaseException as e:  # an unplanned exit is an oracle fault
        print(f"oracle fault: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(2)
ORACLE
