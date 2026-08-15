#!/usr/bin/env bash
# Blind checkpoint — sitting-close deltas (v2: riders sid added
# after 2026-08-15-tarball-riders-003 applied)
# Planner-authored, blind. Thin: append-only growth, the three
# session sids in the record, the INDEX true-up's durable pointer.
set -uo pipefail
fail=0
check() {
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then echo "[PASS] $label"; else echo "[FAIL] $label"; fail=1; fi
}
M=claude/MASTER.md
I=claude/INDEX.md
[ -f "$M" ] || { echo "[FAIL] missing $M"; exit 1; }
[ -f "$I" ] || { echo "[FAIL] missing $I"; exit 1; }

# Append-and-annotate never shrinks the record.
check "MASTER.md grew (>= 132161 bytes pre-session)" \
  bash -c '[ "$(wc -c < claude/MASTER.md)" -ge 132161 ]'

# The three applied sessions are in the record by sid.
for sid in 2026-08-14-global-doc-selfcontainment-006 \
           2026-08-15-claude-core-first-001 \
           2026-08-15-doc-mechanization-002 \
           2026-08-15-tarball-riders-003; do
  check "MASTER.md records $sid" grep -Fq "$sid" "$M"
done

# The de-novo label-cap ratification is recorded with its constant.
check "label-cap discharge names the constant (40)" \
  bash -c "grep -i 'label' '$M' | grep -q '40'"        # wording proxy

# The race evidence entry exists.                       # wording proxy
check "race evidence recorded" grep -qi "race" "$M"

# INDEX true-up points at the guard test's durable home by name.
check "INDEX.md names the guard test" \
  grep -Fq "test_global_doc_selfcontainment" "$I"

exit $fail
