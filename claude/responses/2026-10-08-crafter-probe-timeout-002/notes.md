# notes.md — 2026-10-08-crafter-probe-timeout-002

All three outcomes landed as the brief drew them, plus the mint.
`bin/VERSION` read `0.4.51` before I started, so the brief's §3 gate was clear.
Two things deserve your eye. I found one real bug while building, the
paste-into-a-terminal case below, and fixed it. And I added one piece of
behaviour the brief didn't name: the group kill for background
leftovers.

## Decisions to ratify (brief §8)

- **Default bound: 120 seconds**, the desk's number. It is stated in a
  new fifth line of the purpose header, after the verbatim read-only
  line, so lines 1–4 keep their positions:
  `# Bound: probe() gets 120 seconds of wall clock; BALE_PROBE_TIMEOUT=<seconds> overrides it, BALE_PROBE_TIMEOUT=0 runs it unbounded.`
  The number lives once in the crafter, as `PROBE_DEFAULT_TIMEOUT_SECONDS`.
- **How the bound is applied: the whole body, one bound.** probe()
  runs in a child bash, `bash -c "$(declare -f probe)"`, under
  `timeout -k 5 <bound>`. A shell function can't be handed to
  `timeout` directly; a child bash can. coreutils' `timeout` puts that
  child in its own process group and signals the group, so a
  grandchild (`sleep`, `git`) dies too and the `$(...)` capture
  returns. The worst case is bound + 5 s, if the body ignores TERM.
  I chose a whole-body bound over a per-command one because the
  operator's question is "how long can this paste take", and one
  number answers it.
  - **Consequence for authors:** probe() no longer sees variables or
    functions defined outside it. I made this the same in every path,
    bounded or not, so its semantics never depend on the variable, and
    the scaffold's comment says to keep everything inside probe().
    The scaffold has always put the sections inside probe(), but a
    hand-written probe that leans on a top-level variable would now
    see it unset, so it is a real change.
- **Exit status when the bound bites: unchanged.** Nothing at the
  script's top level calls `exit`. A courier who pastes the block into
  an interactive shell is running it *in* that shell, and `exit 124`
  would close their terminal. So the status stays the clipboard
  tail's, 0 in practice. The cut is reported by the marker inside the
  block and by a `[probe] probe() was cut at its N-second bound …` line
  on stderr.
- **The marker line:**
  `*** PROBE CUT: probe() hit its N-second bound and was stopped; the lines above are partial. Rerun with BALE_PROBE_TIMEOUT=<seconds> for longer, or BALE_PROBE_TIMEOUT=0 for no bound. ***`
  It joins the captured output, so `emit_probe_block` stays
  byte-identical and its trailer counts the marker like any other
  line. A cut is recognised as timeout's 124/137 together with elapsed
  time ≥ the bound, so a body that merely ends on a command returning
  124 isn't mislabelled.
- **`-I` and `PYTHONDONTWRITEBYTECODE`.** Both emitters print
  `python3 -I -B -`. `-B` stays spelled out because `-I` ignores every
  `PYTHON*` variable, `PYTHONDONTWRITEBYTECODE` included. The
  why-comments beside `RECONCILE_EPILOGUE` and in `_doc_assert_block`
  say what `-I` closes: `python3 -` puts the staging root on
  `sys.path[0]`. A new test plants a `json.py` that raises in the
  staging root and runs the reconciliation. On 0.4.51 the plant is
  imported; on 0.4.52 it isn't.
- **The reworded comment:** `# Label column is capped: one pathological
  label must not drag every` / `# row's alignment out. A label past the
  cap still prints in full —` … re-wrapped, rule unchanged. The
  emitted epilogue has no `fold-in` and no `008`. The two source
  comments 0.4.49 reworded are untouched.

## Found while building

- **History expansion ate the block.** My first marker was
  `!!! PROBE CUT …`. Run as `bash probe.sh` it was fine. Pasted into an
  interactive bash (I simulated one with `script`), the `!!` expanded to
  the previous command and overwrote `$out`: the block came back as one
  garbled line, its trailer counting 1. The marker now uses `***`. `$!`
  and `[!…]` are exempt from history expansion, so they were never at
  risk, but the case patterns use `[^…]` anyway. The source comment
  records why. I did not write a unit test for the interactive paste
  (it needs a pty); the `!`-free marker is pinned instead
  (`test_body_never_waits_on_a_terminal_by_construction`).
- **Background leftovers (added beyond the brief).** A body that runs
  `cmd &` and returns leaves `cmd` holding the capture pipe, and the
  `$(...)` waits for it, bound or not. Under `timeout` the body has its
  own process group, so once the body returns the scaffold kills that
  group (`kill -- -$pid`, only when bounded). A test pins it. The case
  isn't covered with `BALE_PROBE_TIMEOUT=0` or with no `timeout`,
  because there is no group to kill there.

## Assumptions worth knowing

- **busybox `timeout`** (Alpine) does not, as far as I know, signal a
  process group. There, a cut kills the child bash, but a grandchild
  may hold the capture until it exits. Your WSL2 Ubuntu has GNU
  coreutils, so this is a note, not a problem. An old busybox whose
  `timeout` rejects `timeout N cmd` is detected by a no-op trial run
  and reported, and the body runs unbounded rather than not at all.
- `gtimeout` is accepted where `timeout` is absent (macOS with
  Homebrew coreutils). With neither, the scaffold prints
  `[probe] no timeout command here …` and runs unbounded.
- An empty-but-set `BALE_PROBE_TIMEOUT=` counts as a bad value: it is
  reported and the default holds.
- `ssh` and `sudo` read passwords from `/dev/tty`, not stdin, so
  closing stdin doesn't stop them prompting. The bound is what ends
  them; `timeout` also sends SIGCONT, so a body stopped on a tty read
  still dies. The TARBALL.md bullet promises only what holds: `read`
  meets end of input, nothing pages, and git refuses a credential
  prompt.

## Places to look

- `tools/craft_response.py`: the comment block above
  `PROBE_DEFAULT_TIMEOUT_SECONDS` / `PROBE_SCAFFOLD` (line 461).
  The bounded capture is between `probe()` and `emit_probe_block`.
  Also the two `-I` lines (684, 2786), and the docstring sentence in
  the "(probe, §4.2)" paragraph.
- `docs/TARBALL.md` 4.2 (after Integrity trailer) and 4.3 (after
  Logged). `validation.sh` removes the two bullets and checks that the
  result hashes to the request's `c32a8dc8…`.
- `tests/test_craft_response.py`: `CraftProbeBound`, right after
  `CraftProbeMode`.

## Validation

I ran `validation.sh` twice from staging-shaped copies with the filled
manifest at `.bale-manifest.json`, `PATH` holding no `bale`:

- **Staged (change applied):** exit 0. Every check `[PASS]`, the
  `--slow` entry `[SKIP]`; claims `[agree]`, the slow one `[n/a]`
  (its claim is observed from the discover run below).
  No `__pycache__` afterwards.
- **Unmodified 0.4.51 base:** exit 1. These failed, as they should:
  `file syntax (py, json)` (no `0.4.52.json`), the VERSION and
  changelog asserts, the TARBALL.md insertion assert, the probe header
  and pinned-bytes asserts, the cut / zero / stdin / bad-value probe
  runs, `-I`, and no-citation. These passed on both, by design,
  because they pin what must not move: the three suite checks (the
  base runs its own older suite), the four global docs, the probe's
  default path for a quick body, the epilogue and doc blocks mapped
  back, and the other emissions.
- The seven unchanged-emission pins (skeleton, `--changes-only`,
  `--apply-only`, `--light-block`, `--bundle` stdout and bundle file,
  `--emit-block`) hash identically from both crafters. `--emit-block`
  is compared with its clock-stamped `created_at` line and its
  body-hash trailer dropped, the only two lines that differ run to run.
- Against the 0.4.51 crafter, the new and moved tests in
  `test_craft_response.py` fail (12 failures, 2 errors). The two that
  pass there pin unchanged behaviour (the default path for a quick
  body, the fixed lines).
- **Whole suite, discover form, on the modified tree:** 2002 tests,
  48 skipped, green, in 871 s here, with `PYTHONDONTWRITEBYTECODE=1`
  exported and no `__pycache__` left behind. The `--slow` claim is
  `pass`/observed from that run. Without the flag it reconciles `[n/a]`.

`model_identity` is the session's configured model id; the serving
model can differ from it.

## Proposals

- **A pty-driven paste test for the probe scaffold.** *What:* a test
  in `tests/test_craft_response.py` that feeds the emitted script,
  line by line, to an interactive `bash -i` on a pseudo-terminal
  (stdlib `pty`), and asserts the block, the shell surviving, and no
  history-expansion damage. *Why:* the one real bug this session hit,
  `!!` in the marker, shows only when the probe is pasted into an
  interactive shell, which is how couriers run it. Nothing in the
  suite exercises that path; this session pinned the symptom (no `!`
  in the marker) rather than the path. *Scope:* the suite only; the
  test must skip cleanly where no pty is available.
