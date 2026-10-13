# notes — 2026-10-13-planner-practices-004

One file changes: `docs/PLANNER.md`, inside its forecast. All fourteen
brief blocks are in, at the anchors and in the order the brief gave. No
light block was needed; no guard refused anything.

## How the blocks landed

- **Extracted, not retyped.** A small script pulled the fourteen
  ```` ```text ```` fences out of the brief and inserted them at the
  brief's anchors. Before inserting, it asserted that each anchor
  matches exactly once inside the right `## N.` section and that the
  neighbouring bullet on the other side is the one the brief names.
  `validation.sh` embeds the same blocks, generated from the brief the
  same way (JSON-escaped inside a quoted heredoc so every byte
  survives).
- **Wrap width 68.** That is the file's real column: only 7 of the
  660 core lines run past 68. Lines break only at spaces, never on a
  hyphen and never inside a backtick span, so whitespace folding
  gives back each block byte-exact. One visible effect: in block 10,
  `unshare -rpf --mount-proc` sits whole on its own continuation line,
  so the line above it runs short. I chose that over splitting the
  code span.
- **Block 1** needed no re-wrap above it. The appended sentence fits
  on the bullet's old last line, at exactly 68 columns.
- **Block 13** is its own paragraph, with a blank line on each side,
  between step 6 and "The rest of the retry…".
- Headings: the same 29 heading lines in the same order (checked by
  hash). No version bump.

## Pins and suites

- I read every `PLANNER.md` pin in the four doc-pin suites by grepping
  each mention with context, not by reading the files top to bottom.
  The pins are presence and order checks on text this session leaves
  alone (the bundle-ruling lead before "Commands are single-line", the
  sanctioned-pair phrases, the §10 floor), plus the
  self-containment deny scan over the new text. The four suites:
  75 tests, all passing on both the base tree and the landed tree.
- Whole suite (`python3 -m unittest discover -s tests`, with
  `PYTHONDONTWRITEBYTECODE=1`, in a scratch repo built from the
  request's `context/`): `Ran 2037 tests`, `OK (skipped=48)`,
  on the landed tree and the base tree alike (about 890 s each).
  None of the arc's known missing-file baseline failures showed up, as
  the brief predicted.
  It takes more than ten minutes here, so `validation.sh` runs only the
  four pin suites, as the brief asks, and stays inside the two-minute
  budget (TARBALL.md §7.6).

## Validation rehearsal

I ran `validation.sh` in a staged copy of each tree. On the landed
tree it exits 0 and all four claims agree. On the unmodified tree it
exits 1: every block-presence probe fails (0 of 48 `ok` lines), and
the other three checks pass. That split is intended. The heading-list
check and the DOCS.md/CODE.md hash check guard constraints the brief
pins as "untouched", so they should pass on both trees. Only the block
check detects the change. Mutation check: changing "licence" to
"license" in block 2 makes it fail by name, and a doubled space in
block 13 folds away, matching the brief's folding rule.

One probe needed fixing during the rehearsal. The "opens a `- **`
bullet line" probe first matched on a block's first three words. Block
6's first three words, "A brief that", also open the existing
"ships no Y" bullet, so the probe passed on the base tree. It now
matches the whole bold lead.

## Assumptions

- The `twine-surface-row` session has landed. The request's AGENT.md
  and TARBALL.md match the provenance `contract_docs` stamps, and
  TARBALL.md §7.1 already has the PID-namespace worker paragraph. So
  block 10's rehearsal half lands next to its worker half, as the brief
  planned.

## Proposals

- **What:** decide whether PLANNER.md §4's new "Rehearse under the
  sandbox's PID namespace" bullet and TARBALL.md §7.1's "The scripts
  run in a PID namespace" paragraph count as a sanctioned pair. If
  they do, register them in DOCS.md §9's list and in
  `tests/test_sanctioned_pairs.py`. If not, cut one down to a pointer.
  **Why:** once landed, the two state the same facts (runner as pid 1,
  inherited group id reads 0, `os.setsid()` or a spawned child,
  `unshare -rpf --mount-proc`) in near-identical words. DOCS.md §9's
  one-home rule allows that only for registered pairs that must agree,
  and nothing would catch the two drifting apart. The brief split the
  item as "worker half there, rehearsal half here", but block 10 as
  ruled restates both halves. I landed it verbatim as instructed; I'm
  flagging the overlap, not disputing the ruling. **Scope hints:**
  `docs/DOCS.md` §9, `tests/test_sanctioned_pairs.py`. That needs a
  session whose forecast includes DOCS.md, which this one's did not.
