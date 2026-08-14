# Notes — 2026-08-14-bare-pack-oneshot-003

**Compaction disclosure (CLAUDE.md §11.6).** The runtime compacted
this session mid-build — after the reading and the first edits, before
the response assembly. I followed the recovery path: re-grounded from
the request manifest, the revG brief, and the partial working tree on
disk (which was authoritative and intact — the full test suite re-ran
green from it), and every hash and claim in this manifest was
re-derived from the finished `files/` bytes after the compaction, per
§11.6 and §10.1 step 10 — nothing was carried from memory. The
`feedback.self_reported.compaction_occurred` flag points here.

**Stretch item dropped.** The handoff read-side parity item is dropped
per the brief's own rule — the §11.2 pre-flight said the core plus the
wizard and echo fit comfortably, the stretch did not earn the margin.

Everything else in the brief landed: Change C whole, both refusal-text
sites, the wizard prompt, the identity echo, the drop-log
summarization, the rider, VERSION → 0.4.10, and the tests (18 new in
`tests/test_checkpoint_file_flag.py`, sentinels updated in
`tests/test_per_sid_checkpoint.py`). Full suite: 441 green. All
changed paths are inside the forecast (`BALE.md`, `bin`, `tests`) — no
drift to admit. The schema constraint verified as expected: no schema
change at all; the json-report keys are docstring-governed, not
schema-governed.

## Judgment calls worth your eyes

- **`locate_inbound_path` split in `bin/bale`.** The wizard checkpoint
  prompt must re-prompt on a search miss, but `resolve_inbound_path`
  fail()s there. Rather than duplicate the search chain or catch
  SystemExit, I split the resolution into a non-failing core
  (`locate_inbound_path`, returns None on a miss) and made
  `resolve_inbound_path` a thin wrapper adding the fail. One
  implementation, two postures; every existing caller is
  byte-identical in behavior.
- **A working-tree file at the resolved path.** The brief specified
  the committed-bytes branches; it didn't say what to do when an
  *uncommitted* file already sits at the resolved path. I applied the
  same never-silently-replace posture one rung earlier: identical
  bytes proceed (write skipped, add+commit runs), differing bytes
  refuse loudly naming both sides. Silently clobbering a working-tree
  file felt like exactly the class of surprise the flag's refusals
  exist to prevent.
- **The post-wizard `[r]` contradiction.** The brief pins the
  `--read-only` + `--checkpoint-file` contradiction at arg-parse; the
  wizard's `[r]` session-shape answer creates the same contradiction
  discoverable only post-wizard. I refuse there too, same message plus
  a remedy naming the wizard answer. The alternative — silently
  dropping the typed flag — is a silent skip.
- **The wizard prompt does not special-case an already-committed
  checkpoint.** It still asks; an empty answer then passes the
  pre-flight exactly as before (the prompt text says so). Skipping the
  prompt on "already committed" would have made the idempotent re-run
  of an aborted wizard pack ask a *different* question sequence than
  the first run, which felt worse than one extra Enter.
- **The echo's path is the resolved SOURCE path** (where the file was
  read from), not the in-repo resolved path — evidence 45's ambiguity
  is *which downloaded file resolved*, and the in-repo path already
  appears in the provenance stamp line. The sha256 is of the read
  bytes, which the install contract makes identical to the committed
  blob's and the stamp's.
- **Summarization threshold is strictly >1.** A single drop keeps the
  0.4.9 per-file line verbatim (its sentinels — the path, the basis,
  the remedy — all survive), so the only behavior change is the
  many-drop wall the architect hit. The summary fires even on a
  hard-breach-shortened walk: whatever dropped before the break is
  still named.
- **Commit subject format** is `bale: per-session checkpoint for
  <sid>` — the `bale:` prefix matches the gitignore auto-commit's
  existing style, and the commit is pathspec-limited so a dirty tree's
  other staged work is untouched (tested).

## Corrective re-issue (same session, `corrects` set)

The blind checkpoint's HOLD was anchor 3 — a planner-side brief defect
(the anchors section present in revC–revE was dropped from revF/revG),
so the sentence never reached me. This re-issue adds it to BALE.md §8.5
verbatim, as one unwrapped physical line, matching the standalone-line
convention anchors 1 and 2 already use; both of those are untouched.
`validation.sh` gains a `grep -Fx` assertion on the exact line so a
future rewrap fails loudly rather than reaching the checkpoint. Nothing
else changed: `bin/`, `tests/`, and the rest of BALE.md are
byte-identical to the held response, and the checkpoint's remaining
assertions (unexecuted on the held tree — it fails fast) are covered
behaviorally by the same green suites as before. Placement judgment
call: §8.5 (the per-session checkpoint contract's home) right after the
one-command install prose; move it if the checkpoint expects it
elsewhere — the assertion travels with the sentence, not the section.
