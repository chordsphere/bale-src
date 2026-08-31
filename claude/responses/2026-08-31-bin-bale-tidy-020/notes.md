# notes — 2026-08-31-bin-bale-tidy-020

Both one-liners landed as accepted; two things to ratify or glance at,
one proposal.

**Item 2's site — a judgment call to ratify.** Board 60 says "the
clarification next-step hint," singular, but `_session_state_and_hint`
has three clarification branches (awaiting planner, awaiting worker,
unreadable side). I put the recovery mention in the **awaiting-worker**
branch only: it's the one state whose hint tells the operator to carry
a paste block they may no longer have — `bale relay` emitted it once on
stdout when the answer was recorded, which is exactly the "staring at
status wondering how to regenerate a block" scenario the proposal
names. The awaiting-planner state reads its questions from the
preserved records on disk, and the unreadable-side branch already
points at inspecting the record directly, so neither got the sentence.
If you want it in all three, that's a trivial follow-up — say so at
review. The wording appends to the existing parenthetical:
"(a further round enters via `bale relay <sid> <file|->`; lost the
block? `bale relay <sid>` alone re-emits it)".

**Tests, per the brief's constraint.** No existing suite could be
extended because no test files were shipped in this request and the
manifest scopes everything except `bin/bale` out; `validation.sh`
instead carries a source-level assertion per edit (both observed
passing in a simulated staging before shipping, and both observed
*failing* against the unmodified `bin/bale`, so they test the change
rather than tautology).

**Claims basis.** All three claims are annotated
`claim_basis: "observed"` — validation.sh ran here against the overlay
plus `apply.sh` before packing.

## Proposals

**What:** One-line docstring touch-up in `bale_pack.py`'s
`persist_pack_session`: the `command` paragraph still reads
"cmd_handoff passing \"handoff\" is proposed but not yet wired
(bin/bale is out of the board-63 session's scope), so handoff opens
stamp \"pack\" until that one-word change lands" — stale the moment
this response merges.
**Why:** The docstring is the parameter's contract of record; a reader
tracing a `"handoff"` stamp back to it would be told the stamp can't
exist yet. Noticed while confirming the parameter's semantics for
item 1; left untouched as out of scope ("everything except bin/bale").
**Scope hints:** `bin/bale_pack.py` (one docstring paragraph); only
after this session lands.
