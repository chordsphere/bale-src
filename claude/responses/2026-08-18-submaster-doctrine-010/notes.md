# notes.md — 2026-08-18-submaster-doctrine-010

The eight verbatim lines were extracted mechanically from the
brief's VERBATIM blocks (never retyped) and spliced in byte-exact;
validation carries a wrap-normalized byte check per line, plus the
flat-clause absence check, plus the three doc suites. Everything I
claimed I also ran locally against a staged copy of the applied
tree (claim_basis: observed).

Judgment calls you should be able to find without reading the diff:

- **§20's number and placement.** The new sub-master section is
  numbered 20 — the next free number — but physically placed in the
  core, between §6 and §7, because a splitting session doing core
  authoring work is its reader. META's core description and the
  PAST-THE-CORE banner both now say "1 through 7, and 20" and the
  banner carries the one-line explanation (stable numbering per
  DOCS.md §6.4, placement follows readers). If you'd rather the
  section sit physically at the end, it's a pure relocation — no
  renumbering either way.
- **K6 landed in §2** (command/request authoring) as "The desk
  default is smaller sessions" — it's a pack-sizing default, so the
  authoring-practice section seemed like its home over §6 or §20.
  K5 landed in §4 as a new bullet right after the imagined-surfaces
  bullet, whose dry-run practice it extends.
- **§7 row 2 reworded.** The old row said "authoring delegation
  stops at commands and briefs", which the ratified doctrine now
  contradicts; it now reads "No session authors an oracle it builds
  against — spawn-material authorship (§20) reaches children's
  checkpoints, never the authoring session's own." The enforcement
  cell is unchanged. This is in-forecast (docs/) but it's a hard-
  rules row, so look at it.
- **K5's provenance landed generically.** The brief's parenthetical
  named a session id (continue-plan-005) and a carry-forward
  number; the globals cite evidence generically and never name
  session ids, so the bullet closes with "Earned at a live
  rehearsal-stub correction." Say the word if you want the id in.
- **"board row 54" in a global doc** — the read-only-waiver
  sentence cites it as queued, per the brief. Precedent exists
  (TARBALL.md already says "board 33" twice), so I followed the
  brief as written rather than genericizing.
- **The fifth-pair pin is one-sided by construction** and the
  suite's comment says so, per the rider: the suite reads docs/
  only, so the project-side twin's half stays pinned project-side.
  The enumeration pin is now 5 and the failure text says "five".
- **No pinned extract was touched by the K2 landing** — the
  existing rescope-pair pins sit in §11.2/§3.4 text I didn't edit,
  so no propagation beyond the deliberate K7/K8 additions was
  needed.

No out-of-forecast paths: all four changes sit inside the stamped
forecast (the `docs` directory entry covers the three docs;
`tests/test_sanctioned_pairs.py` is named). Nothing deferred, no
proposals — the arc-oracle mechanical half is already queued (board
row 54) and stays out of scope here.
