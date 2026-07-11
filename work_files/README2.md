# 2026-07-10 (part 2) — Reversibility Checker: Implementation to Working Pipeline

Continuation of `work_files/2026-07-10_reversibility_classifier/` (files
01–29). That batch ended at the design/implementation-start stage
(`decision_25` through `decision_29`). This batch carries it through to a
tested, end-to-end working pipeline, both single-rule and genuine
multi-rule compound cases.

All setter v0.6 (`prepare`/`run`/`import_prior_commit`/`reuse`, shared
`claims_registry.json`).

## Sequence

| # | File | Status | Note |
|---|------|--------|------|
| 30 | decision_30_ers_setter_gap_candidates | active | Four candidate ERS protocol additions identified from this session's own logic failures — three were later independently built into v0.5/v0.6 by the ERS maintainers |
| 31 | decision_31_ruleset_substrate_plan_continuation | active | Grounds `apply_compound`'s real aggregation before the footprint-wiring attempt |
| 32 | decision_32_reverse_fire_orchestrator_implemented | **superseded by 43** | First `reverse_fire` implementation — coarse footprint approximation, later replaced |
| 33 | decision_33_schema_precompute_unchanged_design | active | Sven's idea: schema-precompute bijective + matching-spectrum candidates for unchanged-node detection |
| 34 | decision_34_unchanged_candidates_verified | active | `compute_unchanged_candidates` implemented and verified both directions (mismatch correctly excluded, match correctly included) |
| 35 | decision_35_isomorphism_check_design | active | Anchor-from-confirmed-unchanged, build-and-compare design (Sven's hints) |
| 36 | decision_36_isomorphism_implemented_and_tested | **superseded by 43** | First `check_isomorphism_anchored` — per-match `rebuild()`, `len(matches)==1` gate |
| 37 | decision_37_per_match_naming_correction | active | `per_rule_multiplicity` → `per_match_multiplicity` (Sven caught the imprecise name — it's keyed by match instance, not rule identity) |
| 38 | decision_38_step4_overlap_comparison_malformed_diagnosis | active (diagnostic) | Sven: "step 4 sounds malformed" — confirmed: the flattened overlap-signature comparison discarded pairing data `detect_overlaps` already provides |
| 39 | decision_39_step4_overlap_comparison_fixed | **active, authoritative** | Direct comparison of `overlapping_nodes`/`boundary_crossings`, no flattening |
| 40 | decision_40_first_genuine_compound_test | active | First real two-rule overlapping test — found and fixed an own construction bug (wrong edge direction) before it passed |
| 41 | decision_41_apply_compound_stub_correction | **active, authoritative** | Corrects an earlier mischaracterization (checker had claimed `apply_compound` needed unbuilt `LayeredGraph` integration from reading only its signature) — built `PlainGraphLayeredStub`, reuses the real `apply_compound` unmodified |
| 42 | decision_42_full_wiring_plan | active | Plan to rewire the whole pipeline through `apply_compound` |
| 43 | decision_43_full_wiring_complete_and_tested | **active, authoritative, current** | Complete rewrite tested against both single-rule (pass) and two-rule compound (correctly rejected, with the rejection traced and explained) cases |
| 44 | decision_44_precise_footprint_wiring_superseded_by_43 | **superseded by 43** | Intermediate schema-precompute-based footprint precision step, since replaced wholesale by `apply_compound`'s exact aggregation |

## Current authoritative state (read these first)

- `decision_39` — overlap comparison
- `decision_41` — why `apply_compound` is reusable directly
- `decision_43` — the complete, tested pipeline

Superseded: `decision_32`, `decision_36`, `decision_44` — kept for the
failure-mode history (Sven caught real mistakes at each: an unwired coarse
approximation, an N=1 gate that turned out unnecessary, and a schema-level
precision effort that a simpler `apply_compound`-based approach fully
subsumed).

## Code (in `code/`, final state as of this batch)

- `reversed_rule.py` — `build_reversed_graph2` (role-swap, category
  transposition, physical-switch `confirmed_crossings` fix),
  `footprint_is_consistent`, `compute_unchanged_candidates`,
  `NotReversibleError`.
- `reverse_compound.py` — `build_reversed_operation`,
  `collect_reversed_matches`, `resolve_reverse_compound`,
  `compute_s_forward`, `reverse_fire`, `check_isomorphism_anchored`.
- `compound_stub.py` — `PlainGraphLayeredStub`, `SimpleRegistry`: minimal
  adapter letting the real `apply_compound` (schema.py, unmodified) run
  against a plain `PerspectiveGraph` for one throwaway compound resolution.

None of these three files are committed to the `perspective` repo yet —
Sven manages git pushes manually. This batch (like part 1) is prepared for
that, not pushed by Claude.

## Tested, verified this batch (not merely designed)

- Single-rule case: `reverse_fire` → `reversible: True`, anchor confirmed,
  `born_correspondence` empty.
- Two-rule genuine compound case (a real `boundary_crossings` overlap,
  confirmed via `detect_overlaps` itself, not a trivial/empty comparison):
  `reverse_fire` → `reversible: False`, traced to a real, explained cause
  (rule A's own declared spectrum doesn't account for structure added to
  its matched node as a side effect of rule B's redirect resolution) — not
  a crash, not an arbitrary rejection.
- `apply_compound` correctly detects and raises on a genuinely cyclic
  mutual boundary-crossing construction (two rules whose live crossings
  each touch the other's own matched node) rather than silently producing
  a wrong result.

## Still open, not resolved by this batch

- Whether reversing an acyclic forward compound structure can ever
  introduce a *new* redirect cycle on the reverse side (untested).
- No test against any real production rule (`spine_finalise_v1.py`,
  `spine_addinit_v4.py`, etc.) — only synthetic toy rules built by hand.
- Zero-anchor frequency and overlap-count distribution in real firings
  remain unmeasured.
- Neither `reversed_rule.py`/`reverse_compound.py`/`compound_stub.py` nor
  this work_files batch is committed to GitHub yet.
