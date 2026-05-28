# INDEX.md

> Drill-down map for this project's documentation.
> Updated whenever the inventory changes.

This is bale-src — the source repo for the bale CLI. The project itself
evolves through bale-on-bale sessions, so the doc inventory is small and
will stay that way for a while.

## Tool design

- `BALE.md` (repo root) — the bale tool's canonical design document.
  Covers purpose, scope, command surface, wire format, pack and apply
  pipelines, rollback/revert/unlock semantics, the bale-enforced
  contract (§11), self-applicability, build phases, and open decisions.
  Pull whenever a session touches `bin/bale`, the pack or apply
  pipeline, the staging or lock lifecycle, the wire format, or the
  bale-enforced contract. Both `bin/bale` (section references in
  comments and docstrings) and the global docs (`TARBALL.md` §7/§8,
  `CLAUDE.md` §5) reference BALE.md directly. Not injected into
  requests for other projects — it is bale-src's project documentation,
  peer in structure to the global workflow docs but project-local.

## Explainers

- `context/bale-internals.md` — how `bin/bale` is structured (commands,
  control flow, configurables), the `bale.toml` schema, and the hook
  contract. Pull when a session touches `bin/bale`, the configurables
  mechanism, or a new hook.
- `context/meta-sessions.md` — the recursive properties every bale-src
  session inherits from working on bale itself: the one-apply-behind
  fixed-point, `bin/bale` as both tool and artifact, the reinstall loop
  that closes the recursion. Pull when packing or reviewing a session
  that touches `bin/bale`, the apply or pack pipeline, the staging
  lifecycle, or the `post_apply_pass` hook.

## Notes on this index

The global docs (`CLAUDE.md`, `TARBALL.md`, `DOCS.md`, `CODE.md`) ship from
the bale installation and are injected into every request; they are not
listed here. `BALE.md` is listed because it lives in this repo and is the
canonical design reference for the bale tool — it is project
documentation for bale-src, not a global workflow doc, and is not
injected into requests for other projects.

Routing — when a session is authoring or emitting a `bale pack` command
(by hand, or as a rescope offer per `CLAUDE.md` §11.2), the canonical
flag/format surface is `TARBALL.md` §3.4; cite it rather than reconstruct
the command from `bin/bale`'s pack argparse parser, which now carries a
pointer comment to the same section. This is a cross-reference into an
injected global doc, not an inventory entry — the global docs are not
listed here (see above).

Per DOCS.md §4.1, INDEX.md is usually introduced once a project has ~3+
findable docs. This one was introduced early, on architect's call so the
scaffolding would be in place when more arrived. The current inventory
is BALE.md plus two explainers; further explainers will likely arrive
alongside the apply search-paths mechanism or a new hook.

BALE.md is a category-of-one for bale-src: structurally peer to the
global workflow docs (own META + INDEX + numbered sections) but
project-local and not injected. DOCS.md's inventory table doesn't get
a new row for it because adding bale-src-specific categories to a
project-agnostic doc would itself be the wrong direction; this hint
here in `INDEX.md` is the discoverable surface.
