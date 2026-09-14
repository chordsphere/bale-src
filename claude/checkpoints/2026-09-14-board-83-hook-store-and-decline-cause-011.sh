#!/usr/bin/env bash
# Blind checkpoint — row 83 (hook store view + decline cause), v1.
# Authored at the 2026-09-14-continue-plan-006 sitting from the
# request, before implementation. Outcome contracts only:
#   1. tests/test_hook_acceptance.py runs green;
#   2. the three VERBATIM decline-cause phrases are present in bin/bale
#      and the bare cause-less line is gone (preserved text);
#   3. `bale config hooks --help` parses (exit 0) — the verb exists;
#   4. bin/bale no longer spells response-NNN.tar.gz.
# Deliberately no bin/VERSION probe: this session is bumpless and its
# sibling bumps, so a version probe would couple to apply order.
# Writes: nothing outside the suite's temp dirs.
set -u
status=0
pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; status=1; }
if [ ! -f bin/bale ] || [ ! -d tests ]; then
  echo "[FAIL] checkpoint must run at the repo root"; exit 2
fi
joined() { python3 -c "import re,sys; print(re.sub(r'\"\s*\n\s*\"','',open(sys.argv[1]).read()))" "$1"; }

# 1. Suite.
out="$(python3 -m unittest discover -s tests -p 'test_hook_acceptance.py' 2>&1)"
if [ $? -eq 0 ] && echo "$out" | grep -q '^OK'; then
  pass "test_hook_acceptance green"
else
  echo "$out" | tail -n 8; fail "test_hook_acceptance not green"
fi

# 2. Cause phrases (VERBATIM from the brief) and the retired bare line.
for phrase in \
  "declined (stdin closed or interrupted); not invoking." \
  "declined (empty answer at a decline default); not invoking." \
  "declined (answered '"; do
  if joined bin/bale | grep -Fq -- "$phrase"; then
    pass "bin/bale carries: $phrase"
  else
    fail "bin/bale lacks: $phrase"
  fi
done
if joined bin/bale | grep -Fq -- "declined; not invoking."; then
  fail "bin/bale still carries the cause-less 'declined; not invoking.' line"
else
  pass "the cause-less decline line is gone"
fi

# 3. The verb exists.
if python3 bin/bale config hooks --help >/dev/null 2>&1; then
  pass "bale config hooks --help exits 0"
else
  fail "bale config hooks --help does not parse"
fi

# 4. Help strings.
if joined bin/bale | grep -Fq -- "response-NNN.tar.gz"; then
  fail "bin/bale still spells response-NNN.tar.gz"
else
  pass "bin/bale no longer spells response-NNN.tar.gz"
fi

exit "$status"
