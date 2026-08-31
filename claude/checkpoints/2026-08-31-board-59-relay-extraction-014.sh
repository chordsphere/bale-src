#!/usr/bin/env bash
# Blind checkpoint — board-59-relay-extraction (rev1).
# Authored at the 2026-08-31-continue-plan-012 sitting, from the
# request, before implementation. Outcome contracts only — the
# suites and behavior parity are validation.sh's lane.
# Runs with cwd = the staged (applied) tree. Exit: 0 pass, 1 a probe
# failed, 2 this script itself errored.
set -u

fails=0
ok()   { echo "[CKPT PASS] $1"; }
bad()  { echo "[CKPT FAIL] $1"; fails=$((fails + 1)); }

# Outcome 1: the module exists.
if [ -f "bin/bale_relay.py" ]; then ok "relay-module-exists"; else bad "relay-module-exists"; fi

# Outcome 2: the module is well-formed Python.
if [ -f "bin/bale_relay.py" ]; then
  if python3 -c "import ast,sys; ast.parse(open('bin/bale_relay.py').read())" 2>/dev/null; then
    ok "relay-module-parses"
  else
    bad "relay-module-parses"
  fi
else
  bad "relay-module-parses"
fi

# Outcome 3: the relay verb survives the move (CLI surface intact).
if python3 bin/bale relay --help >/dev/null 2>&1; then
  ok "relay-verb-alive"
else
  bad "relay-verb-alive"
fi

# Outcome 4: packaging parity — the new shipped file is named in the
# install and build surfaces.
if grep -qF "bale_relay.py" install.sh; then ok "install-names-module"; else bad "install-names-module"; fi
if grep -qF "bale_relay.py" scripts/build.sh; then ok "build-names-module"; else bad "build-names-module"; fi

if [ "$fails" -gt 0 ]; then
  echo "[CKPT] $fails probe(s) failed"
  exit 1
fi
echo "[CKPT] all probes passed"
exit 0
