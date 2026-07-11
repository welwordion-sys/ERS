# 2026-07-10 (part 3) — Reversibility Checker: Real-Data Bugs, Step 5 Redesign, Dispatch Attempt

Continuation of part 2 (files 01–45). Part 2 ended with the classifier
working end-to-end against one real production rule. This batch covers
everything found and fixed by actually running it against real data and
by Sven's direct design pushback, through to the dispatch/grouping
optimization attempt.

## Sequence

| # | File | Status | Note |
|---|------|--------|------|
| 46 | decision_46_correct_pipeline_integration | active | Corrects the real caller: match-all → compound-fire → then-check, not a stop-at-first-match loop |
| 47 | decision_47_pipeline_corrected_tested | active | Verified against real production case with the corrected pipeline |
| 48 | decision_48_born_node_reversal_gap | active (superseded finding, correct diagnosis) | Traced a real False verdict to its exact mechanism: forward-born node wrongly survived in reverse, real prior node wrongly consumed |
| 49 | decision_49_construction_defect_not_special_logic | **active, corrects framing** | Sven: reverse firing isn't special — `apply_compound`/`compile_core` are firing-agnostic. The defect is in `build_reversed_graph2`'s construction, not a missing "reverse mode" |
| 50 | decision_50_born_delete_duality_fix | **active, authoritative** | The actual, much simpler fix: reverse `core.inherit` only, not `core.mapping_in`. Born↔delete duality falls out for free. Verified against the real case that exposed the bug |
| 51 | decision_51_born_mapping_precision | active (correction, then retracted scope) | Sven: born nodes DO have mapping edges — corrected a mischaracterization. Opened a "derivation-consistency" concern |
| 52 | decision_52_course_correction_merge_edges | **active, retracts 51's concern** | Sven: merge/creation edges functionally disappear on reversal by their nature — nothing to verify. The "derivation-consistency" idea was scope creep, not a real gap |
| 53 | decision_53_step5_redesign_question | active | Sven's critique: step 5 was existence-only, not correspondence. Design for exact preserved-id-set comparison, split/merge-tolerant |
| 54 | decision_54_step5_implementation | active | Concrete design: per-instance id-set equality (pairing already fixed by construction, no search needed) plus firing-count backstop |
| 55 | decision_55_step5_verified | active | Implemented and verified against synthetic regression and the real production case |
| 56 | decision_56_forced_born_filter_fix | **active, authoritative** | Found while explaining split/merge to Sven: the id-set check didn't account for `apply_compound`'s `forced_born` override (genuine `overlapping_nodes` conflicts). Fixed using the already-computed `born` aggregate |
| 57 | decision_57_forced_born_fix_verified | active | Verified against real `apply_compound` output from a constructed conflict — logic confirmed correct in isolation; full end-to-end pipeline test through this exact path still open |
| 58 | decision_58_dispatch_optimization_attempt | active (honest negative result) | Fingerprint-gate pre-filter verified CORRECT (no false negatives against real data) but provides NO benefit for the tested case — skipped 0/257 rules, net slower. Real pruning would need the CoreTree's shared-core walk, not attempted |
| 59 | decision_59_final_integration | **active, authoritative, current** | The real integration point: `reclassify_after_firing` wraps `apply_compound`, running `reverse_fire` after firing and upgrading the poisoned-apple `UPWARD` default to `SIDEWAYS` (provenance dropped) when proven reversible. Tested three ways: known-reversible, known-not-reversible, and the real production case through actual `LayeredGraph`/`LayerRegistry` |

## Real caller, finally

`reclassify_after_firing(lg, registry, base_layer, new_layer, matches)` in
`reverse_compound.py` is the answer to "who calls this." Both
`apply_compound` and `layer_apply_schema` unconditionally write every new
`LayerRecord` as `UPWARD` with provenance attached — confirmed by reading
both call sites. Nothing anywhere ever called the "prove it's actually
reversible" step. This wrapper is that step: fires normally via the real,
unmodified `apply_compound`, then runs `reverse_fire` on the same matches
and the actual before/after graphs, and — **only on a strict `True`**, never
on `False` or `"unverifiable"` — replaces the registry's record with
`SIDEWAYS`/`provenance=None`, exactly matching `LayerRecord`'s own
validation invariant (a sideways layer's source is recoverable via the
ruleset inverse, so provenance would be redundant).

Required one small, additive change to `layers.py`:
`LayerRegistry.reclassify(key, record)`, since `add()` forbids overwriting
an existing key.

**Named scope limit, not silently claimed done:** only `apply_compound`
(the compound path) is wrapped. `layer_apply_schema` (the single-rule
firing path) is not — a real gap for single-rule firings specifically.

## Current authoritative state (read these first)

- `decision_50` — the actual born/delete fix (reverse `inherit` only)
- `decision_52` — merge edges need no verification; task scope is inherit + boundary/crossings, nothing more
- `decision_56` — the forced-born filter fix for genuine `overlapping_nodes` conflicts

## Code (in `code/`, final state as of this batch — supersedes part 2's `code/`)

- `reversed_rule.py` — **changed**: `build_reversed_graph2` now reverses `core.inherit` only (was `core.mapping_in`, the actual bug).
- `reverse_compound.py` — **changed**: `_preserved_ids_per_instance` (exact per-instance id-set check, forced-born-aware), `reverse_fire` reordered, and the new `reclassify_after_firing` — the real integration point.
- `compound_stub.py` — unchanged from part 2.
- `layers.py` — **changed**: added `LayerRegistry.reclassify(key, record)`, small and additive.
- `check_real_rule_reversibility.py` — unchanged from part 2 (superseded by v2, kept for history).
- `check_real_rule_reversibility_v2.py` — the corrected three-phase caller (match-all → fire → check). Note: this and `check_real_rule_reversibility.py` are standalone diagnostic scripts (unguarded top-level execution, no `if __name__ == '__main__':`) that don't cleanly belong in either `builders/` (wrong purpose — that directory is rule-construction and arithmetic-correctness testing) or `basic_machinery/` (wrong kind — every file there is a pure importable library module). Real caller integration is now `reclassify_after_firing`, not these scripts.

## Real bugs found this batch, all via actually running against production data or Sven's direct pushback

1. Real caller didn't reflect the actual firing pipeline (stop-at-first-match instead of match-all-then-fire).
2. `build_reversed_graph2` reversed the wrong dict (`mapping_in` instead of `inherit`) — the actual root cause of a real False verdict on `add_init_00_single_single`.
3. Step 5 (`per_match_multiplicity`) was existence-only, not correspondence — Sven's critique, confirmed accurate.
4. The id-set check didn't account for `forced_born` overrides in genuine `overlapping_nodes` conflicts.
5. The reversibility checker had no real caller anywhere — every `LayerRecord` was hardcoded `UPWARD`, forever, regardless of actual reversibility.

## Still open after this batch

- Forced-born fix verified in isolation against real `apply_compound` data, not yet through a full end-to-end `reverse_fire` run (no distinguishable-but-conflicting rule pair successfully constructed yet).
- Dispatch/grouping optimization: attempted, verified correct, verified NOT beneficial for the tested case; real tree-sharing-based pruning not built.
- `layer_apply_schema` (single-rule firing path) is not wrapped with the same reclassification `apply_compound` now gets.
- No test against any rule beyond `add_init_00_single_single`.
- The two `check_real_rule_reversibility*.py` scripts have no proper home in this codebase's structure yet.
- Nothing in this repo's code is committed to GitHub yet — a stray `test_branch_creation.txt` was accidentally left on `main` this session and needs manual removal.
