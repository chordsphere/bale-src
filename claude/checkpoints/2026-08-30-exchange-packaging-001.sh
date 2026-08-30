#!/usr/bin/env bash
# Blind checkpoint — exchange-packaging (2026-08-29), v1. Outcome-only;
# read-only. Exit 0 all pass, 1 any fail, 2 script error.
set -u
echo "checkpoint exchange-packaging v1: writes to no location"
fail=0
pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; fail=1; }
probe() { local l="$1"; shift; if "$@" >/dev/null 2>&1; then pass "$l"; else fail "$l"; fi; }
present() { local l="$1" n="$2" f="$3"; [[ -f "$f" ]] && grep -qF -- "$n" "$f" && pass "$l" || fail "$l"; }
present "build.sh RELEASE_FILES lists the exchange schema" "schemas/exchange-record.schema.json" scripts/build.sh
present "install.sh INSTALL_LAYOUT lists the exchange schema" "schemas/exchange-record.schema.json" install.sh
present "packaging suite pins the exchange schema" "exchange" tests/test_release_packaging.py
probe "release packaging suite passes" python3 -m unittest discover -s tests -p test_release_packaging.py
probe "full unit suite passes" python3 -m unittest discover -s tests
probe "bin/VERSION unchanged at 0.4.18" grep -qF 0.4.18 bin/VERSION
exit $fail
