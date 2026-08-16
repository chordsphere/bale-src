# notes.md — 2026-08-16-sitting-close-deltas-005

## Transport correction (recording as instructed by the desk relay)

The shipped brief (`README.md` in the request) was stale: the pack's
`--readme-file` search path resolved an earlier download predating the
brief's sections 4–5, which is why the manifest goal named four
deliverables and the shipped file carried three. Sections 4–5 were
supplied by desk relay in chat (`close-session-relay.md`),
byte-verbatim from the authored brief — the relay states sha256
ffa09e5298e2c0bb22aa1754851495ff379acb3b7a8b9cb1b06fea9f6bd221e0 for
the full authored file. I verified my landed text against the relay's
copy mechanically (whitespace-normalized equality per block); I could
not verify the relay against the authored file itself, having only the
relay.

## Clarification round, resolved in chat (recorded per TARBALL.md §5.9.1)

Two blocking questions were asked in chat pre-build; the desk's
answers, which this response proceeds on:

1. **Judgment-call block content** — missing from the shipped brief;
   supplied as relay section 4b, landed as written.
2. **Ratification word** — given explicitly: *ratified, 2026-08-16*;
   the pack is the act, the brief header's "pending" language is stale
   drafting context. Relay section 4a **supersedes the shipped brief's
   section 2** as the queue-reorder record's form — section 2 was not
   landed; 4a was.

## The one edit outside the brief's blocks

The header's `Last landed by:` line was edited in place from
`...-001` to `...-005`, per the doc's own recorded convention ("this
line is edited in place at each landing") — pre-cleared by the desk in
the relay (item 3). Everything else is pure insertion: validation.sh's
append-only check proves every pre-existing line survives in order.

## Placement and formatting judgment calls (the brief named no anchors
for the relay sections — review these first)

- **4a + 4b → §3's end**, after the 2026-08-14/15 judgment-calls
  block, before "## 4. The board" — matching where §3's sitting
  landing records and their judgment-call blocks accrete.
- **4b's lead-in**: the relay's `### 4b.` heading is brief
  scaffolding; its title text landed as the block's lead-in line with
  a colon added ("Judgment calls, dated 2026-08-16 at the master
  desk:"), parallel to the existing "Ratified judgment calls, one
  line each, dated …" lead-ins. 4a's heading ("superseding form") was
  dropped as pure scaffolding; the body stands alone.
- **4c → second bracket after the charter bracket**, immediately
  following the brief-section-3 "ratified at the sitting open"
  bracket — chronological order (ratified, then EXECUTED), both
  before the "**Added at the 2026-08-14/15 improvement sitting**"
  run-in.
- **4e → last fold-in registry entry**, before the
  cleared-at-this-landing blocks; the relay heading text serves as
  the entry name, body verbatim.
- **4d → top of §6**, its own paragraph between the heading and the
  "1–9 carried forward" paragraph; "one line" landed as one sentence
  wrapped to the file's column convention.
- **Re-wrapping**: all blocks re-wrapped to the file's ~72-column
  convention and, for the board-10 brackets, the queue entry's
  6-space continuation indent. Wording is byte-verbatim after
  whitespace normalization — checked mechanically during the build
  and again by validation.sh's presence assertions.

## Claims basis

Checks 1–2 are claimed `observed`: I ran the shipped validation.sh in
a simulated staging (git checkout of the shipped MASTER.md base with
the change applied) and both passed; a negative test (removing one
pre-existing line) confirmed the append-only check actually fails
when violated. Check 3 is claimed `predicted`: in real staging it
reads `git show HEAD:claude/MASTER.md`, and I can't observe the
repo's HEAD — if anything landed on MASTER.md after this request
packed, the check will fail, and that disagreement would be the
diagnostic doing its job.

## Scope

One change, `claude/MASTER.md`, inside the recorded forecast. No
out-of-forecast paths.

## Proposals

- **What:** Extend the Evidence-45 publish-the-sha/compare-the-echo
  practice from checkpoints to briefs mechanically: a
  `--readme-sha256 <hash>` companion to `--readme-file` that makes
  pack refuse when the resolved file's hash disagrees — or fold
  README candidates into the queued "candidate picker" rider's
  newest-first listing (path, mtime, sha prefix).
  **Why:** This session is a live specimen: the search path resolved
  a stale download, the pack report's echoed sha256 (v0.3.21) was
  available but nothing compared it, and the miss cost a
  clarification round. The desk published the authored brief's
  sha256 in the relay — the practice half already exists; only the
  mechanical half is missing.
  **Scope hints:** `bin/bale_pack.py` (`--readme-file` resolution),
  the pack report echo; adjacent to the wizard checkpoint
  candidate-picker rider (same registry list), so possibly the same
  carrier.
