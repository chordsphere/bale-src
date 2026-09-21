#!/usr/bin/env bash
# Blind checkpoint, v1 — board 103's doc lane (slug board-103-doc-lane).
# Authored 2026-09-21 by the master 2026-09-21-continue-plan-005, from the
# request, before any implementation exists.
#
# Outcome-only: it reads docs/TARBALL.md and docs/CLAUDE.md in the tree it
# is run from and asserts what must be true of them. It writes nothing,
# imports nothing local, and needs no network. Verdict lines are
# label-only. Exit 0 = every probe passed; 1 = at least one probe failed;
# 2 = the script errored or its own control failed (a defective oracle).
set -u
exec python3 -B - <<'PYEOF'
import re
import sys

TARBALL = "docs/TARBALL.md"
CLAUDE = "docs/CLAUDE.md"

V1 = ("The block reaches chat as a file: redirect `--emit-block` to a file "
      "and present that file. A block typed inline instead must keep every "
      "`\\uXXXX` escape as an escape, because the body is ASCII-escaped and "
      "the trailer hashes those bytes; and on a trailer refusal the worker "
      "re-presents the file and never retypes the block.")
V2 = ("Every outcome the brief pins \u2014 a verbatim block, a byte-for-byte "
      "constraint, an untouched file \u2014 gets an assertion that compares "
      "bytes; a comparison made through `$(...)` is newline-blind, because "
      "command substitution strips trailing newlines.")
# Preserved text (the base's own bytes, which the worker carries anyway).
HOLD_PARA_OPEN = ("A HOLD reaches the worker as one addressed block that "
                  "`bale apply` prints between the whole-line sentinels")
ROUTE_11_4 = "Shape and required artifacts: `TARBALL.md` section 5.6."
DENY = ("sonnet", "fable", "opus", "haiku", "open-weight", "open weight",
        "capability probe")


def norm(text):
    return re.sub(r"\s+", " ", text).strip()


def section(text, heading_re):
    """Body under the first heading line matching heading_re, up to the
    next heading of the same or a shallower level. None when absent."""
    m = re.search(heading_re, text, re.M)
    if m is None:
        return None
    level = len(re.match(r"#+", m.group(0)).group(0))
    rest = text[m.end():]
    nxt = re.search(r"^#{1,%d}\s" % level, rest, re.M)
    return rest if nxt is None else rest[:nxt.start()]


def before_subheading(body):
    """The part of a section body ahead of its first deeper heading."""
    nxt = re.search(r"^#+\s", body, re.M)
    return body if nxt is None else body[:nxt.start()]


def step(body, n):
    """Numbered list item n of a section body: from its `n. ` line to the
    next top-level numbered item. None when absent."""
    m = re.search(r"^%d\.\s" % n, body, re.M)
    if m is None:
        return None
    rest = body[m.end():]
    nxt = re.search(r"^\d+\.\s", rest, re.M)
    return rest if nxt is None else rest[:nxt.start()]


def paragraphs(body):
    return [p for p in re.split(r"\n\s*\n", body) if p.strip()]


def has_phrase(body, phrase):
    return re.search(r"(?<![A-Za-z])" + re.escape(phrase), norm(body),
                     re.I) is not None


def control():
    """Prove the extractors on a synthetic doc. A failure here is the
    oracle's defect, never the work's."""
    doc = ("## 5. Five\nlead\n### 5.4 Notes\nalpha `path`\n#### 5.4.1 Sub\n"
           "beta\n### 5.5 Next\ngamma\n## 7. Seven\nseven lead\n### 7.1 One\n"
           "1. first has a file\n2. second as a\n   file here\n3. third\n"
           "## 8. Eight\n")
    s54 = section(doc, r"^### 5\.4 .*$")
    s7 = section(doc, r"^## 7\. .*$")
    s71 = section(doc, r"^### 7\.1 .*$")
    ok = (
        s54 == "\nalpha `path`\n#### 5.4.1 Sub\nbeta\n"
        and before_subheading(s54) == "\nalpha `path`\n"
        and s7 is not None and "### 7.1 One" in s7 and "Eight" not in s7
        and section(doc, r"^### 9\.9 .*$") is None
        and step(s71, 2) == "second as a\n   file here\n"
        and step(s71, 4) is None
        and has_phrase(step(s71, 2), "as a file")
        and not has_phrase(step(s71, 1), "as a file")
        and has_phrase("An Interpreter\ncache", "interpreter cache")
        and paragraphs("a\n\nb c\n\n\nd") == ["a", "b c", "d"]
        and norm(" x\n  y ") == "x y"
    )
    return ok


def main():
    if not control():
        print("checkpoint control failed: the oracle's own extractors "
              "misbehave", file=sys.stderr)
        return 2
    try:
        with open(TARBALL, encoding="utf-8") as fh:
            tarball = fh.read()
        with open(CLAUDE, encoding="utf-8") as fh:
            claude = fh.read()
    except OSError as exc:
        print("checkpoint cannot read its inputs: %s" % exc, file=sys.stderr)
        return 2

    sec = {
        "5.4": section(tarball, r"^### 5\.4 .*$"),
        "5.9.2": section(tarball, r"^#### 5\.9\.2 .*$"),
        "7": section(tarball, r"^## 7\. .*$"),
        "7.1": section(tarball, r"^### 7\.1 .*$"),
        "7.2": section(tarball, r"^### 7\.2 .*$"),
        "10.1": section(tarball, r"^### 10\.1 .*$"),
        "10.3": section(tarball, r"^### 10\.3 .*$"),
        "INDEX": section(claude, r"^## INDEX\s*$"),
        "11.4": section(claude, r"^### 11\.4 .*$"),
    }
    steps = {}
    if sec["10.3"] is not None:
        steps = {n: step(sec["10.3"], n) for n in (1, 2, 3, 4, 5)}
    missing = [k for k, v in sec.items() if v is None]
    missing += ["10.3 step %d" % n for n, v in steps.items() if v is None]

    results = []

    def probe(label, needs, check):
        """needs: section keys (or step numbers) the probe reads. A probe
        whose surface is missing SKIPs by name, so one missing heading is
        one FAIL, not a cascade."""
        lost = [str(k) for k in needs
                if (sec.get(k) is None if isinstance(k, str)
                    else steps.get(k) is None)]
        if lost:
            results.append(("SKIP", label + ": its section is missing"))
            return
        results.append(("PASS" if check() else "FAIL", label))

    results.append(("PASS" if not missing else "FAIL",
                    "touched sections and steps keep their numbers"))

    probe("TARBALL 5.9.2 carries VERBATIM-1", ["5.9.2"],
          lambda: norm(V1) in norm(sec["5.9.2"]))
    probe("TARBALL 10.3 step 4 names file delivery", ["10.3", 4],
          lambda: has_phrase(steps[4], "as a file"))
    probe("TARBALL 5.4 names forecast_departures and its two keys", ["5.4"],
          lambda: all(tok in before_subheading(sec["5.4"])
                      for tok in ("`forecast_departures`", "`path`",
                                  "`why`")))
    probe("TARBALL 10.1 names forecast_departures", ["10.1"],
          lambda: "`forecast_departures`" in sec["10.1"])
    probe("TARBALL 7.2 carries VERBATIM-2", ["7.2"],
          lambda: norm(V2) in norm(sec["7.2"]))
    probe("TARBALL 7.1 names the usual surprise write", ["7.1"],
          lambda: has_phrase(sec["7.1"], "interpreter cache"))
    probe("CLAUDE INDEX settles the DOCS.md trigger", ["INDEX"],
          lambda: has_phrase(sec["INDEX"], "user-facing doc"))
    probe("TARBALL 5.9.2 marks the PLANNER.md 15 pointer", ["5.9.2"],
          lambda: any("\u00a715" in p and has_phrase(p, "planner-side")
                      for p in paragraphs(sec["5.9.2"])))
    probe("TARBALL 10.3 step 3 routes planner context", ["10.3", 3],
          lambda: "`context`" in steps[3])
    probe("TARBALL 7 states the unmodified-tree run", ["7"],
          lambda: has_phrase(sec["7"], "unmodified tree"))
    probe("TARBALL 7 lead keeps the worker relay paragraph", ["7"],
          lambda: HOLD_PARA_OPEN in norm(before_subheading(sec["7"])))
    probe("CLAUDE 11.4 still routes to TARBALL 5.6", ["11.4"],
          lambda: ROUTE_11_4 in norm(sec["11.4"]))
    low = (tarball + "\n" + claude).lower()
    results.append(("PASS" if not any(
        re.search(r"(?<![a-z])" + re.escape(word) + r"(?![a-z])", low)
        for word in DENY) else "FAIL",
                    "the two docs carry no model or run names"))

    for verdict, label in results:
        print("[%s] %s" % (verdict, label))
    return 1 if any(v == "FAIL" for v, _ in results) else 0


try:
    sys.exit(main())
except SystemExit:
    raise
except Exception as exc:  # the script itself errored: exit 2, never 1
    print("checkpoint errored: %r" % (exc,), file=sys.stderr)
    sys.exit(2)
PYEOF
