# notes.md — 2026-08-14-global-doc-selfcontainment-006

Everything landed in-forecast: `BALE.md`, `docs/TARBALL.md`, and the
new test under `tests/` (directory forecast covers it). Three things
to ratify, one verification report, and one small observation.

## A thirteenth citation site (deviation from the brief's enumeration)

The brief enumerates twelve `BALE.md` sites; grep confirms exactly
those twelve, and all are handled per the brief's per-site treatment.
But the manifest goal says *every project-local citation*, and §5.9.2
carried a thirteenth the enumeration missed: the deferral to
`claude/context/orchestration.md` §8 "(in bale's source repo)" for
the options/recommendation/priority doctrine. Same dangling-pointer
problem, same fix: the deferral now reads "has one home in the bale
tool's own orchestration documentation." The one-home fact and the
this-section-stops-here scoping both survive; only the project-local
name and section dropped. Ratify or correct — reverting this one line
is trivial if you'd rather it ride another session.

Consequently I also added `orchestration.md` to the guard test's deny
list (not in the brief's three-entry spec). It's a bale-src project
doc with no legitimate generic use in the globals, and the list stays
explicit and simple. Drop the entry if you disagree; the test is a
one-line edit.

## The INDEX.md pin: `claude/INDEX.md`, not bare `INDEX.md`

The globals mention `INDEX.md` 36 times, all as the generic
project-map concept, which the brief says stays legal. The
citation-shaped form I pinned is the literal substring
`claude/INDEX.md` — the path-qualified spelling a reference to
bale-src's own doc map would take, which appears zero times in the
globals today. This stays a plain substring on the deny list rather
than a heuristic. Residual risk: future generic prose could
legitimately produce that substring (DOCS.md does say the project map
typically lives at `claude/`), in which case the test fails loudly
and the prose gets reworded or the entry gets dropped — a
false-positive that announces itself, not a silent one. If you'd
rather not carry that risk, delete the entry and the test pins the
brief's fallback position (BALE.md + MASTER.md, plus orchestration.md
per above).

## Dropped alongside site 3: the telemetry record path

The §5.3 parenthetical carried `attempts[].validation.claims` as well
as the cite. I dropped the whole parenthetical: the key path is
telemetry-record shape — a contract on the bale implementation, not
on the worker — and the worker-facing fact (verbatim promotion, so
ship-time declarations are measurable record-side) survives in the
sentence. If you want the record path kept worker-visible, it can
come back without the cite.

## Content-loss verification for the tombstone rewrites

Per the brief's "verify, don't duplicate": §5.9.3's old tombstone
named the `.bale/clarifications/` preservation path and the lock
retention. Both facts already live where the new tombstone points —
lock-stays-held and continues-to-a-normal-response in §5.9's intro
prose, the `.bale/clarifications/` aggregation surface in §5.9.4 — so
nothing was inlined and nothing was lost. `validation.sh` asserts the
survivals.

## Guard test verified in both directions

Green against this change set; red (2 failures, naming the offending
lines) against the pre-session `docs/TARBALL.md`. Discovery mode and
direct-module mode both pick it up. It's harness-free on the
`test_schema_embeds.py` precedent — pure file reads, no subprocess,
hermetic by construction, so ADR-0005's sandbox machinery isn't
needed.

## Observation, no action taken

§5.8 and §5.9.2 still say the two schema files are "in bale's repo."
Those are install artifacts (the `schemas/` tree ships in the
install, and `response_lint.py` embeds both), so they're reachable
from any project and I read them as install-local like the `tools/`
citations, not project-local — outside this goal. If you want the
phrasing tightened to "in the bale installation," that's a two-line
follow-up; not worth a Proposals entry.
