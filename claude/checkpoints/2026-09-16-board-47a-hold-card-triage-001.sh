#!/bin/bash
# Blind checkpoint — board 47a (HOLD-card triage: judge line, failed
# probe labels, ruling-forked successors, telemetry field), v1.
# Outcome-only: drives one HOLD apply through the staged bin/ in a
# scratch repo (delivery dir with a space, so quoting shows). cwd =
# staging root; nested bale runs --no-sandbox under this checkpoint's
# own confinement.
fails=0
pass() { echo "[PASS] $1"; }
failp() { echo "[FAIL] $1"; fails=$((fails+1)); }
ROOT="$PWD"; BALE="$ROOT/bin/bale"; CR="$ROOT/tools/craft_response.py"
S="$(mktemp -d /tmp/oracle-47a.XXXXXX)"; trap 'rm -rf "$S"' EXIT
export HOME="$S" GIT_CONFIG_NOSYSTEM=1
R="$S/repo"; DL="$S/my dl"; mkdir -p "$R/src" "$R/claude/checkpoints" "$DL" "$S/resp/files/src" "$S/pkg"
echo 'x = 1' > "$R/src/a.py"
( cd "$R" && git init -q && git config user.name o && git config user.email o@o && printf '[staging]\nstrategy = "target-base"\n[apply]\nsearch_paths = ["%s"]\n[validation]\nbase = "claude/checkpoints/{sid}.sh"\n' "$DL" > bale.toml && git add -A && git commit -qm init ) || { failp "scratch repo"; exit 1; }
printf '#!/bin/bash\necho "[FAIL] oracle-probe-alpha"\necho "[PASS] oracle-probe-beta"\nexit 1\n' > "$S/ck.sh"
( cd "$R" && python3 "$BALE" pack "hold me" --slug oracle --include src --write src/a.py --no-readme --checkpoint-file "$S/ck.sh" </dev/null >"$S/pack.out" 2>&1 ) || { failp "scratch pack"; exit 1; }
SID="$(grep -o 'session id: *[0-9a-z-]*' "$S/pack.out" | head -1 | sed 's/.*: *//')"
[ -n "$SID" ] || { failp "scratch sid"; exit 1; }
echo 'x = 2' > "$S/resp/files/src/a.py"
python3 "$CR" "$S/resp" --sid "$SID" --write >/dev/null 2>&1
python3 - "$S/resp/manifest.json" <<'PY'
import json, sys
p = sys.argv[1]; m = json.load(open(p)); m.pop("action", None)
m["summary"] = "oracle"; m["validation_will_run"] = ["oracle-check"]; m["claims"] = {"oracle-check": "pass"}
for c in m["changes"]: c["action"] = "modified"; c["reason"] = "oracle"
json.dump(m, open(p, "w"), indent=2)
PY
printf '#!/bin/bash\necho "[PASS] oracle-check"\nexit 0\n' > "$S/resp/validation.sh"; chmod +x "$S/resp/validation.sh" "$S/resp/apply.sh"
cp -r "$S/resp" "$S/pkg/response-$SID" && tar -czf "$DL/response-$SID.tar.gz" -C "$S/pkg" "response-$SID"
HELD="$DL/response-$SID.tar.gz"; Q="'$HELD'"
( cd "$R" && python3 "$BALE" apply "response-$SID.tar.gz" --no-sandbox </dev/null >"$S/apply.out" 2>&1 ); rc=$?
[ "$rc" -eq 1 ] && grep -q "\[HOLD\] $SID" "$S/apply.out" || { failp "scratch apply reached a HOLD (exit $rc)"; exit 1; }
# The card region: everything from the first "[HOLD] <sid>" line to the end (both HOLD blocks).
CARD="$(awk -v sid="$SID" '!on && $0 ~ "\\[HOLD\\] " sid {on=1} on {print}' "$S/apply.out")"

# P1: the card names the failed probe label.
if printf '%s' "$CARD" | grep -q 'oracle-probe-alpha'; then pass "HOLD card names the failed probe label"; else failp "HOLD card names the failed probe label"; fi
# P2: the card's judge line attributes the HOLD to the checkpoint, not the worker's exit.
if printf '%s' "$CARD" | grep -q 'checkpoint: HOLD (exit 1)' && printf '%s' "$CARD" | grep -q 'worker validation: PASS' && ! printf '%s' "$CARD" | grep -q 'validation: exited 0'; then pass "HOLD card judge line attributes the ruling per source"; else failp "HOLD card judge line attributes the ruling per source"; fi
# P3: no placeholder successor; both ruling-forked successors composed and quoted.
if ! printf '%s' "$CARD" | grep -q '<new-tarball>'; then pass "no <new-tarball> placeholder on the card"; else failp "no <new-tarball> placeholder on the card"; fi
if printf '%s' "$CARD" | grep -qF "bale retry $Q --accept-checkpoint-change"; then pass "fixture-defect successor composed and quoted"; else failp "fixture-defect successor composed and quoted"; fi
if printf '%s' "$CARD" | grep -F "bale retry $Q" | grep -qv -- '--accept-checkpoint-change'; then pass "work-defect successor composed and quoted"; else failp "work-defect successor composed and quoted"; fi
if printf '%s' "$CARD" | grep -q 'bale amend-checkpoint'; then pass "fixture-defect rung names amend-checkpoint"; else failp "fixture-defect rung names amend-checkpoint"; fi
# P4: telemetry — failed probe labels additive on the attempt's checkpoint; the two promoted fields.
if python3 - "$R/claude/telemetry/$SID.json" <<'PY'
import json, sys
a = json.load(open(sys.argv[1]))["attempts"][-1]
ok = a["checkpoint"].get("failed_probes") == ["oracle-probe-alpha"]
ok = ok and a["validation"].get("validation_will_run") == ["oracle-check"] and "corrects" in a
sys.exit(0 if ok else 1)
PY
then pass "telemetry attempt carries failed_probes, validation_will_run, corrects"; else failp "telemetry attempt carries failed_probes, validation_will_run, corrects"; fi
# P5: BALE.md riders, verbatim.
if grep -qF 'bale open parses and gates the stored argv — the forecast-existence and forecast-disjointness gates — before the checkpoint dry-run, so an argv defect refuses without spending the oracle.' "$ROOT/BALE.md"; then pass "BALE.md open-order sentence present verbatim"; else failp "BALE.md open-order sentence present verbatim"; fi
if grep -qF 'On a miss, apply, retry, and handoff list every near-name candidate in the searched directories' "$ROOT/BALE.md"; then pass "BALE.md near-name sentence names handoff"; else failp "BALE.md near-name sentence names handoff"; fi
# P6: version.
if [ "$(tr -d '[:space:]' < "$ROOT/bin/VERSION")" = "0.4.34" ]; then pass "bin/VERSION is 0.4.34"; else failp "bin/VERSION is 0.4.34"; fi
[ "$fails" -eq 0 ] && exit 0 || exit 1
