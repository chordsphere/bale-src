#!/usr/bin/env bash
# Blind checkpoint, v1 — the split's role transition, unconditional
# (slug split-transition-unconditional). Authored 2026-09-21 by the master
# 2026-09-21-continue-plan-005, from the request, before any
# implementation exists.
#
# Outcome-only: it reads docs/CLAUDE.md, docs/TARBALL.md and
# docs/PLANNER.md in the tree it is run from and asserts what must be true
# of them. It writes nothing, imports nothing local, and needs no network.
# Verdict lines are label-only. Exit 0 = every probe passed; 1 = at least
# one probe failed; 2 = the script errored or its own control failed (a
# defective oracle).
set -u
exec python3 -B - <<'PYEOF'
import re
import sys

TARBALL = "docs/TARBALL.md"
CLAUDE = "docs/CLAUDE.md"
PLANNER = "docs/PLANNER.md"

VA = ("The offering session delivers that command bundled, in every project "
      "\u2014 as the stored pack argv of a crafter bundle emitted beside its "
      "`bale open` line \u2014 per `PLANNER.md` \u00a720 and \u00a72; the bare "
      "line stays the offer's content, which the planner re-derives from "
      "(`TARBALL.md` \u00a73.4).")
VB = ("The split is always a role transition (`PLANNER.md` \u00a720): the "
      "offering session, as sub-master for its subtree, authors the split "
      "sessions' materials \u2014 commands, briefs, and, in a "
      "checkpoint-configured project, re-derived checkpoints for children it "
      "will not build against \u2014 and holds its decomposition for the "
      "parent's ratification before anything spawns (`PLANNER.md` "
      "\u00a720.1); the operator carries artifacts, never authors them.")
VD = ("In practice: a session that hits the split gate (`CLAUDE.md` "
      "\u00a711.2) does not emit an offer and hand authoring back to the "
      "operator.")
# Preserved text: the base's own bytes, which the worker carries anyway.
OLD_A = ("In a checkpoint-configured project the offering session delivers "
         "that command bundled")
OLD_B = ("In a checkpoint-configured project the split is also a role "
         "transition")
OLD_D = ("hits the split gate (`CLAUDE.md` \u00a711.2) in a "
         "checkpoint-configured project")
CHILD = ("Each child's command is delivered as one crafter bundle emitted "
         "beside its `bale open` line (`PLANNER.md` \u00a72).")
CKPT_LEAD = "**Checkpoint-configured projects.**"
EXAMPLE = "as Claude would emit it in a `CLAUDE.md` \u00a711.2 offer"
OFFER = ("a real, copy-pasteable `bale pack` command the architect can paste "
         "to create the narrower request.")
P2_LEAD = ("**The bundle is the delivery form of every planner-authored "
           "pack, in every project.**")
HOLD_20_1 = ("the parent's ratification of the decomposition, before "
             "anything spawns, is the control.")


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
        docs = {}
        for path in (TARBALL, CLAUDE, PLANNER):
            with open(path, encoding="utf-8") as fh:
                docs[path] = fh.read()
    except OSError as exc:
        print("checkpoint cannot read its inputs: %s" % exc, file=sys.stderr)
        return 2
    tarball, claude, planner = docs[TARBALL], docs[CLAUDE], docs[PLANNER]

    sec = {
        "11.2": section(claude, r"^### 11\.2 .*$"),
        "3.4": section(tarball, r"^### 3\.4 .*$"),
        "P2": section(planner, r"^## 2\. .*$"),
        "P3": section(planner, r"^## 3\. .*$"),
        "P4": section(planner, r"^## 4\. .*$"),
        "P6": section(planner, r"^## 6\. .*$"),
        "P20": section(planner, r"^## 20\. .*$"),
        "P20.1": section(planner, r"^### 20\.1 .*$"),
    }
    ckpt_paras, other_paras = [], []
    if sec["3.4"] is not None:
        for para in paragraphs(sec["3.4"]):
            (ckpt_paras if norm(para).startswith(CKPT_LEAD)
             else other_paras).append(norm(para))
    sec["3.4 checkpoint paragraph"] = ckpt_paras[0] if len(
        ckpt_paras) == 1 else None
    missing = [k for k, v in sec.items() if v is None]

    results = []

    def probe(label, needs, check):
        """A probe whose surface is missing SKIPs by name, so one missing
        heading is one FAIL, not a cascade."""
        if any(sec.get(k) is None for k in needs):
            results.append(("SKIP", label + ": its section is missing"))
            return
        results.append(("PASS" if check() else "FAIL", label))

    results.append(("PASS" if not missing else "FAIL",
                    "touched sections keep their numbers and leads"))

    probe("CLAUDE 11.2 carries VERBATIM-A", ["11.2"],
          lambda: norm(VA) in norm(sec["11.2"]))
    probe("CLAUDE 11.2 carries VERBATIM-B", ["11.2"],
          lambda: norm(VB) in norm(sec["11.2"]))
    probe("CLAUDE 11.2 no longer conditions delivery or the transition",
          ["11.2"],
          lambda: OLD_A not in norm(sec["11.2"])
          and OLD_B not in norm(sec["11.2"]))
    probe("PLANNER 20 opens its practice without the condition", ["P20"],
          lambda: any(norm(p).startswith(norm(VD))
                      for p in paragraphs(before_subheading(sec["P20"])))
          and OLD_D not in norm(sec["P20"]))
    probe("TARBALL 3.4 states bundled delivery outside the checkpoint "
          "paragraph", ["3.4", "3.4 checkpoint paragraph"],
          lambda: any(CHILD in p for p in other_paras)
          and CHILD not in sec["3.4 checkpoint paragraph"])
    probe("TARBALL 3.4 points at PLANNER.md 20 outside the checkpoint "
          "paragraph", ["3.4", "3.4 checkpoint paragraph"],
          lambda: any("`PLANNER.md` \u00a720" in p for p in other_paras))
    probe("TARBALL 3.4's rescope example names the bundle's verb", ["3.4"],
          lambda: EXAMPLE in norm(sec["3.4"])
          and "`bale open`" in norm(sec["3.4"]).split(EXAMPLE, 1)[1])
    probe("PLANNER 4 states the failed-control exit", ["P4"],
          lambda: has_phrase(sec["P4"], "exits 2"))
    probe("PLANNER 3 or 6 places the sequencing line", ["P3", "P6"],
          lambda: has_phrase(sec["P3"], "sitting record")
          or has_phrase(sec["P6"], "sitting record"))
    probe("CLAUDE 11.2 keeps the offer's content", ["11.2"],
          lambda: OFFER in norm(sec["11.2"]))
    probe("PLANNER keeps its unconditional statements", ["P2", "P20.1"],
          lambda: P2_LEAD in norm(sec["P2"])
          and HOLD_20_1 in norm(sec["P20.1"]))

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
