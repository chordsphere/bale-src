#!/bin/bash
# Blind checkpoint — board 96 (doc half) + 97, v1. Outcome-only over the
# staged docs; whitespace collapsed for wrapped prose. cwd = staging root.
fails=0
pass() { echo "[PASS] $1"; }
failp() { echo "[FAIL] $1"; fails=$((fails+1)); }
flat() { tr -s '[:space:]' ' ' < "$1"; }
T="docs/TARBALL.md"; C="docs/CLAUDE.md"; P="docs/PLANNER.md"; D="docs/DOCS.md"
absent() { if flat "$1" | grep -qF "$2"; then failp "$3"; else pass "$3"; fi; }
present() { if flat "$1" | grep -qF "$2"; then pass "$3"; else failp "$3"; fi; }

absent "$T" "small enough to resolve" "TARBALL.md §3.3 size-based chat invitation struck"
absent "$T" "a question in chat as conversation" "TARBALL.md §5.9.1 chat-as-conversation path struck"
absent "$C" "Claude asks, in one sentence" "CLAUDE.md one-sentence mode ask struck"
absent "$C" "brief paused question in chat" "CLAUDE.md paused-question-in-chat invitation struck"
if grep -q '^### 5\.10' "$T"; then pass "TARBALL.md has a §5.10 heading"; else failp "TARBALL.md has a §5.10 heading"; fi
present "$T" "A question set is admitted to the light tier when it holds at most three questions, none multi-tiered, and each carries a default the packer can ratify with a word or an answer that fits on one line; the worker counts, never judges." "§5.10 admission rule verbatim"
present "$T" 'The packer replies in one of three ways: answer inline; "as assumed" to ratify every default at once; or "formal" to have the same questions returned as a clarification response.' "§5.10 three replies verbatim"
present "$C" "5.10" "CLAUDE.md points at TARBALL.md §5.10"
present "$P" '"as assumed"' "PLANNER.md §15 carries the packer's as-assumed reply"
present "$C" "claude/context/adr/NNNN-*.md" "CLAUDE.md INDEX row uses the ratified ADR path"
if grep -q 'relevant `adr/NNNN' "$C"; then failp "CLAUDE.md bare adr/ spelling gone"; else pass "CLAUDE.md bare adr/ spelling gone"; fi
absent "$T" "decisions/" "TARBALL.md §3.1 example no longer says decisions/"
present "$D" "claude/context/adr/NNNN-lowercase-hyphenated.md" "DOCS.md spelling intact"
if python3 -m unittest tests.test_sanctioned_pairs tests.test_doc_crossrefs tests.test_global_doc_selfcontainment tests.test_schema_embeds >/dev/null 2>&1; then pass "doc-pin suites green"; else failp "doc-pin suites green"; fi
[ "$fails" -eq 0 ] && exit 0 || exit 1
