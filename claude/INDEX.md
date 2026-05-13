# INDEX.md

> Drill-down map for this project's documentation.
> Updated whenever the inventory changes.

This is bale-src — the source repo for the bale CLI. The project itself
evolves through bale-on-bale sessions, so the doc inventory is small and
will stay that way for a while.

## Explainers

- `context/bale-internals.md` — how `bin/bale` is structured (commands,
  control flow, configurables), the `bale.toml` schema, and the hook
  contract. Pull when a session touches `bin/bale`, the configurables
  mechanism, or a new hook.

## Notes on this index

The global docs (`CLAUDE.md`, `TARBALL.md`, `DOCS.md`) ship from the bale
installation and are injected into every request; they are not listed
here. Per DOCS.md §4.1, INDEX.md is usually introduced once a project has
~3+ findable docs. This one was introduced early on architect's call so
the scaffolding is in place when the second and third explainers arrive
(probably alongside the post_pack hook and the apply search-paths
mechanism).
