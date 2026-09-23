#!/usr/bin/env bash
# Blind checkpoint — W1 of the 100 arc, the doc sweep (v1).
# Sitting: 2026-09-23-board-100-design-001 (sub-master desk). Authored from
# the W1 request before any worker output existed; rehearsed against the
# 0.4.41 tree (expected HOLD) and a mechanically derived landing.
# Runs cwd = staging (the tree with changes applied). Exit: 0 pass, 1 fail,
# 2 the oracle itself is broken (a failed control, TARBALL.md §7.5).
set -u
status=0
note()   { printf '[ckpt] %s\n' "$*"; }
failck() { printf '[ckpt] FAIL: %s\n' "$*"; status=1; }
broken() { printf '[ckpt] ERROR (oracle): %s\n' "$*"; exit 2; }

GLOBALS="docs/CLAUDE.md docs/TARBALL.md docs/DOCS.md docs/CODE.md docs/PLANNER.md"
SWEPT="$GLOBALS README.md"

# ---------- Controls: the detectors detect ----------
printf 'the Claude reads\n' | grep -qw 'Claude' || broken "noun detector cannot see the token"
printf 'CLAUDE.md claude.ai claude-decides\n' | grep -qw 'Claude' && broken "noun detector matches non-noun spellings"
printf 'bale-injected docs\n' | grep -qwE 'inject|injects|injected|injecting|injection|injections' || broken "inject detector blind"
printf 'INJECTED_TOOLS\n' | grep -qwE 'inject|injects|injected|injecting|injection|injections' && broken "inject detector matches the identifier"
for f in $SWEPT; do [ -f "$f" ] || broken "missing $f in staging"; done
[ -d tests ] || broken "no tests/ in staging"
note "controls passed"

# ---------- 1. The noun is gone from the swept files ----------
hits="$(grep -nw 'Claude' $SWEPT 2>/dev/null)"
if [ -z "$hits" ]; then note "noun sweep complete across the five globals and README.md"
else failck "capitalized Claude remains: $(printf '%s\n' "$hits" | wc -l | tr -d ' ') line(s), first: $(printf '%s\n' "$hits" | head -n 1)"; fi

# ---------- 2. Inject vocabulary is gone (identifier excepted) ----------
hits="$(grep -nwE 'inject|injects|injected|injecting|injection|injections|Inject|Injected|Injection' $SWEPT 2>/dev/null)"
if [ -z "$hits" ]; then note "inject vocabulary gone from the swept files"
else failck "inject vocabulary remains: $(printf '%s\n' "$hits" | wc -l | tr -d ' ') line(s), first: $(printf '%s\n' "$hits" | head -n 1)"; fi
grep -q 'INJECTED_TOOLS' docs/TARBALL.md && note "identifier INJECTED_TOOLS left verbatim for W3" \
  || failck "the identifier INJECTED_TOOLS was rewritten in TARBALL.md; that re-cite is W3's"

# ---------- 3. Surface notes past the core banner ----------
grep -qxF '### 11.7 Surface notes' docs/CLAUDE.md && note "§11.7 heading present, verbatim" \
  || failck "the verbatim heading '### 11.7 Surface notes' is absent from docs/CLAUDE.md"
banner=$(grep -n 'PAST THE CORE' docs/CLAUDE.md | head -n 1 | cut -d: -f1)
first_surface=$(grep -n 'claude\.ai' docs/CLAUDE.md | head -n 1 | cut -d: -f1)
if [ -z "$banner" ]; then failck "no PAST THE CORE banner in docs/CLAUDE.md"
elif [ -z "$first_surface" ]; then failck "no claude.ai row anywhere in docs/CLAUDE.md; the surface table should carry one"
elif [ "$first_surface" -gt "$banner" ]; then note "every claude.ai mention sits past the core banner"
else failck "a claude.ai mention remains in the core (line $first_surface, banner at $banner)"; fi
for f in docs/TARBALL.md docs/DOCS.md docs/CODE.md docs/PLANNER.md README.md; do
  grep -q 'claude\.ai' "$f" && failck "surface name leaked into $f"
done

# ---------- 4. Validate-before-apply reworded, both sites ----------
grep -qF 'Validate before apply, always' docs/TARBALL.md && failck "old row text survives in TARBALL.md §8" \
  || note "old row text gone from TARBALL.md"
grep -qiF 'validate before apply' docs/CLAUDE.md && failck "old operator-discipline phrase survives in CLAUDE.md §6" \
  || note "old phrase gone from CLAUDE.md"
grep -E '^\|.*bale apply.*\|.*operator discipline.*\|' docs/TARBALL.md >/dev/null \
  && note "operator-discipline row names bale apply" \
  || failck "no §8 table row names bale apply under operator discipline"

# ---------- 5. §5.2.2's three field semantics ----------
grep -qF '<vendor>:<model>' docs/TARBALL.md && note "model_identity format token present" \
  || failck "the format token <vendor>:<model> is absent from TARBALL.md"
grep -qF 'decision:' docs/TARBALL.md && note "includes_missing decision marker present" \
  || failck "the entry marker decision: is absent from TARBALL.md"
joined="$(tr '\n' ' ' < docs/TARBALL.md | tr -s ' ')"
case "$joined" in
  *"null for a paste-back probe or an in-chat ask, which resolve within the session"*) note "depends_on sentence transported" ;;
  *) failck "the depends_on sentence (schema :224) is not in TARBALL.md prose" ;;
esac

# ---------- 6. Light-block ledger in PLANNER.md ----------
n=$(grep -ciE 'light[ -]block|light question block' docs/PLANNER.md)
[ "$n" -ge 1 ] && note "PLANNER.md names the light block on $n line(s)" \
  || failck "PLANNER.md names the light block on $n line(s); the §6 ledger bullet is missing"

# ---------- 7. What W1 must not have done ----------
[ -f docs/CLAUDE.md ] && [ ! -f docs/AGENT.md ] && note "file name untouched (W3's)" \
  || failck "docs/CLAUDE.md renamed or docs/AGENT.md created; that is W3's"
n=$(grep -c 'claude-decides' docs/TARBALL.md)
[ "$n" -ge 3 ] && note "enum sites left verbatim ($n lines)" \
  || failck "claude-decides sites in TARBALL.md dropped to $n; those are W3's"

# ---------- 8. Suite green ----------
if python3 -m unittest discover -s tests >/dev/null 2>&1; then note "unit suite green"
else failck "unit suite not green"; fi

exit "$status"
