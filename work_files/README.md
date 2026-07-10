# Work files — Compound Match Resolution session, 2026-07-08/09

Setter v0.3 ground/propose/check/commit ledgers for each design decision made
while implementing Compound Match Resolution (perspective.Compound Match
Resolution, welwordion-sys/perspective). Referenced by filename from that KB
node's `ers_work_files` field — this commit is what makes that reference
resolve to something real instead of a dead pointer.

Order reflects the actual session sequence, not alphabetical:

1. decision_find_all_cores.json       — merge find_all_cores into core_finder.py
                                         as a sibling to find_core, vs. mutating
                                         find_core's contract or a fully separate path
2. decision_schema_reuse.json         — reuse precompiled per-rule schema artifacts
                                         for compound overlap resolution, vs.
                                         authoring/translating a new merged graph2
3. decision_detect_overlaps.json      — detect_overlaps() correctness (both
                                         overlapping_nodes and boundary_of_one_inside_other)
4. decision_resolve_compound.json     — resolve_compound() correctness (forced-born,
                                         redirects); cascade flagged unverified at 2 matches
5. decision_3match_tests.json         — closes the 2-match cascade gap at 3-match
                                         depth (fan-in + combined collision)
6. decision_orchestrator_order.json   — apply_compound's resolution order (topo sort
                                         of redirect deps) and the drop-vs-reattach
                                         rule for a redirect whose owner has no
                                         surviving inherit claim
7. decision_redirect_lookup_investigation.json — a mapping_in fallback was proposed,
                                         disproven against compile_core's actual
                                         partition guarantee, and reverted; the
                                         DROP path was then validated for real

All 7 done under setter v0.3. Superseded by v0.4 as of this session's KB
update (not yet re-verified under v0.4 — see PROTOCOL.md v0.4's I7 for what's
new and would need checking).
