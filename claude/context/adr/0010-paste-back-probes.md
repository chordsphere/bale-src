# ADR-0010: Paste-back probes and default-to-ask engagement

- **Status:** Proposed
- **Date:** 2026-07-07
- **Supersedes:** —
- **Superseded by:** —

## Context

Two problems surfaced with the probe contract as originally written
(TARBALL.md §4, pre-2026-07-07).

**Transport friction.** The probe wrote files to `./probe-output/`
that the architect had to collect and re-upload into the next
request. For the common case — a tool version, a git status, the
contents of one missed file — the file round-trip was heavier than
the information it carried.

**Under-use.** The engagement language ("when, and only when";
"probes are for facts, not for comfort") set a probe-as-last-resort
posture. Observed effect: workers noticing a needed file was absent
from `context/` and working around the gap — reconstructing an API
from memory, guessing between plausible layouts — instead of asking.
That is exactly the confidently-wrong failure mode the workflow
exists to prevent, produced by the doctrine meant to prevent it.

## Decision

1. **Doctrine flip to default-to-ask.** The worker treats the
   architect's environment as its own: anything readable is
   available on request. A missing or stale file, an unknown tool
   version, an unclear working-tree state — each is a probe trigger.
   Working around missing context is reframed as a policy violation,
   not resourcefulness. Two boundaries hold: conceptual/scope gaps
   remain chat conversations, and `expects_probe: no` still forbids
   probing (TARBALL.md §3.3 unchanged).

2. **Paste-back becomes the default probe shape.** One
   self-contained shell block, strictly read-only (zero writes —
   a hardening over the old contract's `./probe-output/` allowance),
   with a purpose header, BEGIN/END sentinels, labeled per-question
   sections, bounded per-command output with explicit truncation
   markers, and an integrity trailer (line count) so a truncated
   paste is detected rather than reasoned from. The architect pastes
   the block into a terminal and pastes stdout back into chat.

3. **The file-based probe survives as the explicit fallback** for
   output whose size or format defeats terminal paste. It keeps the
   old rules: writes only under `./probe-output/`, `meta.json`
   contract, preamble declaring writes and tools. The worker picks
   it only when needed and says so.

4. **Provenance.** Pasted probe output is chat-ephemeral; the
   eventual response's `notes.md` records what the probe
   established — facts relied on, not the raw dump.
   `depends_on.previous_probe` semantics are unchanged; its
   populated case is now mainly the fallback path.

5. **Courier-agnostic.** In the orchestrated workflow the probe
   becomes a harness-executed tool call. Paste-back is the
   manual-transport analog of that call — same contract, different
   courier. The sentinels, bounds, and integrity trailer are the
   properties a machine round-trip needs too.

## Consequences

- More probes are expected. That is the point: probe frequency was
  the wrong minimization target; wrong-response frequency is the
  right one.
- The common probe gets cheaper (paste both ways, no files), and the
  read-before-paste audit gets simpler (zero writes to reason about).
- Doc surfaces updated in the session that lands this ADR:
  TARBALL.md §4 rewritten (with §2, §3.2, §5.1, §8, §10.2
  cross-references aligned), CLAUDE.md's probe posture lines
  (reading principle and INDEX read-paths row), the
  `previous_probe` schema description, and `bale pack`'s
  `--expects-probe` help text. No behavioral CLI changes.
- A truncated or mangled paste is now a detectable condition (the
  integrity trailer) with a defined recovery (re-request), rather
  than a silent half-environment.
- Foreclosed: probe-as-last-resort framing. Any future language
  implying probes are rare or costly should be treated as a
  regression against this decision.
