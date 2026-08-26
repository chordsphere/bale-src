#!/usr/bin/env bash
# Blind checkpoint — harness spec-intake sitting-close deltas landing.
# Authored at 2026-08-26-spec-deltas-001 (read-only desk), from the
# request (the deltas crib), before the implementation exists.
# Outcome contracts on the applied tree only; no mechanism assertions.
# Probes pin preserved identifiers (sids, filenames, item numbers),
# never authored phrasing.
set -u

M="claude/MASTER.md"
fail=0
probe() { # probe NAME COND-EXIT
  local name="$1" rc="$2"
  if [ "$rc" -eq 0 ]; then
    echo "PASS  $name"
  else
    echo "FAIL  $name"
    fail=1
  fi
}

[ -r "$M" ] || { echo "FAIL  master-file-readable ($M missing)"; exit 1; }

# Region slices by strict, byte-stable anchors (section headers are
# stable identities per DOCS.md numbering conventions).
sec4="$(awk '/^## 4\. The board/{f=1} /^## 5\. Contracts established/{f=0} f' "$M")"
sec5="$(awk '/^## 5\. Contracts established/{f=1} /^## 6\. Orchestration-doctrine/{f=0} f' "$M")"
row10="$(printf '%s\n' "$sec4" | awk '/^10\. /{f=1} /^11\. /{f=0} f')"

# Anchor sanity: the slices must be non-empty, or every probe below
# would fail for the wrong reason.
probe "anchor-sec4-nonempty"  "$([ -n "$sec4" ]; echo $?)"
probe "anchor-sec5-nonempty"  "$([ -n "$sec5" ]; echo $?)"
probe "anchor-row10-nonempty" "$([ -n "$row10" ]; echo $?)"

# P1 — §5 gains the spec-intake sitting's ratifications: the sitting
# sid (preserved identifier) appears in the contracts section.
printf '%s' "$sec5" | grep -qF "2026-08-25-harness-discussion-005"
probe "p1-sec5-cites-sitting-sid" "$?"

# P2 — board-10 row records the S6 discharge at that sitting: the
# same sid appears inside the row.
printf '%s' "$row10" | grep -qF "2026-08-25-harness-discussion-005"
probe "p2-row10-cites-sitting-sid" "$?"

# P3 — the row gains the outward pointer to the harness repo's seed
# doc (architect's ruling; filename is a preserved identifier).
printf '%s' "$row10" | grep -qF "harness-seed.md"
probe "p3-row10-outward-pointer" "$?"

# P4 — a new board item 56 exists.
printf '%s' "$sec4" | grep -qE '^56\. \*\*'
probe "p4-board-item-56-exists" "$?"

# P5 — item 56 is the changelog record family item: the block from
# its header to the next item header (or section end) mentions the
# changelog. Topic identity, not phrasing.
printf '%s' "$sec4" | awk '/^56\. /{f=1} /^57\. /{f=0} f' | grep -qi "changelog"
probe "p5-item-56-is-changelog" "$?"

# P6 — the header's last-landed-by line was edited in place: it no
# longer names the previous landing and carries a sid-shaped token.
lline="$(grep -m1 '^Last landed by:' "$M")"
printf '%s' "$lline" | grep -qF "2026-08-25-sitting-close-deltas-010"
old_present=$?
printf '%s' "$lline" | grep -qE '20[0-9]{2}-[0-9]{2}-[0-9]{2}-[a-z0-9-]+-[0-9]{3}'
sid_shaped=$?
probe "p6-last-landed-by-updated" "$([ "$old_present" -ne 0 ] && [ "$sid_shaped" -eq 0 ]; echo $?)"

exit "$fail"
