#!/usr/bin/env bash
# checkpoint-smoothing-close-v2.sh (derives from v1: adds the row-52
# and Block-K probes; all v1 probes byte-identical)
# Blind checkpoint for the 2026-08-18 smoothing-sitting close-deltas
# session. Authored at the master desk from the request before
# implementation. All positive probes pin fixed strings from
# verbatim-marked brief blocks (sanctioned by the provenance-split
# rule: the worker must carry them byte-verbatim anyway); one
# negative probe pins the retired clause's absence. Wrap-tolerant:
# newline-joined before matching. Exit 0 pass, 1 probe failure(s),
# 2 script/tree error.
set -u
f=claude/MASTER.md
if [ ! -f "$f" ]; then
  echo "[checkpoint ERROR] expected file missing: $f"
  exit 2
fi
N="$(tr '\n' ' ' < "$f" | tr -s ' ')"
fail_count=0
probe() {
  label="$1"; pattern="$2"; want="$3"   # want: present|absent
  if echo "$N" | grep -Fiq -- "$pattern"; then found=present; else found=absent; fi
  if [ "$found" = "$want" ]; then
    echo "[probe PASS] $label"
  else
    echo "[probe FAIL] $label"
    fail_count=$((fail_count+1))
  fi
}
probe "row 49 lands (bale open)"                    "bale open" present
probe "rows 36/40/48 convert (ABSORBED)"            "ABSORBED" present
probe "row 39 grows (world-state digest)"           "world-state digest" present
probe "row 47 grows (relay block)"                  "relay block" present
probe "rows 50 lands (CRLF tolerance)"              "CRLF toleran" present
probe "row 51 lands (bare apply resolution)"        "resolves the newest response" present
probe "evidence 80 lands"                           "made the human the mechanism" present
probe "sitting block lands"                         "smoothing sitting" present
probe "row 52 lands (preamble emission)"            "preamble" present
probe "Block K lands (paste-block surface)"         "paste-block surface" present
probe "version-paste rule retired (negative)"       "at each sitting's open" absent
if [ "$fail_count" -gt 0 ]; then
  echo "[checkpoint] $fail_count probe(s) failed"
  exit 1
fi
echo "[checkpoint] all probes passed"
exit 0
