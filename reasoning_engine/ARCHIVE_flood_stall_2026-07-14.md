# ARCHIVED — flood-and-stall reasoning engine (best working version)

STATUS: **ARCHIVED, NOT GATED, NOT DECLARED.** Frozen 2026-07-14 as the
high-water mark of the full-engine line, in case it is resumed. It is not a
result and not a contribution — see "Why archived" below.

## What this is
The flood-and-stall loop (DESIGN_STATE_2026-07-13.md) realized and run to
COMPLETION on a compare goal, after the self-check fixes. Files:
  - flood_stall.py   — the loop: flood/stall/D2-scope/D6-select/emit/resolve
  - prop_counter.py  — propagation counter (force-progression; UNTESTED path)
  - fs_trial.py      — the completing trial (bob/compare, done-state met 1/6 budget)

This is the PATCHED version (D2_PRIMARY explicit, exhausted-set, stuck-predicate),
NOT the earlier trial that failed instructively. The patched version completes.

## Why archived (the honest finding, 2026-07-14)
Three searches + one trial converged on: nothing here is architecturally
genuine vs prior art.
  - The loop IS Means-Ends Analysis (Newell & Simon 1972) + a truth-maintenance
    agenda (Doyle 1979) + HTN subgoal decomposition.
  - The LLM-as-compiler-at-leaves / mechanical-control-everywhere invariant IS
    the published "agentic neuro-symbolic loop" paradigm (2025-26): neural
    generation -> symbolic grounding/validation -> deterministic policy check
    -> feedback. FormalJudge, ANNEAL, etc.
  - Measured wins in that paradigm ALL came from domains with a hard correctness
    oracle (compiler, SMT, functional-equivalence tests). This engine has NO
    such oracle — ERS checks shape, not truth. The parts with evidence behind
    them (a real boundary checker; rollback/provenance) are exactly the parts
    this engine lacks.

## Self-check faults recorded (so a resume does not re-trip them)
  A. (fixed) _mark_dead sentinel corrupted the graph -> exhausted-set instead.
  B. (design hole) no stuck-state predicate; tree-counter bounce was masking a
     missing terminator. Stuck-predicate added; real fix is backtrack/rollback.
  C. (design underspec) "primary relationship" undefined — D2 scope is a set,
     has no order; alphabetical guess mis-picked (diagnose wanted causation,
     got category). D2_PRIMARY map added. THIS starved the goal-relevant
     question until fixed.
  D. (design gap) goal bound at 2 sites, needed 3 — added focus-proximity to D6.
  E. (design unspecified) flood is full-replay each iter -> quadratic; incremental
     vs replay never specified.
  Untested: propagation counter force-progression path never fired in trial.

## If resumed, the two real targets (both evidenced, neither built here)
  1. Grounding at the POPULATION boundary — the unsolved problem in this whole
     paradigm, and the part this engine waves at as "LLM-as-compiler, for now."
  2. Rollback / provenance / validate-before-commit — the component that
     separated the systems that durably worked from the ones that didn't.

## Transplant taken forward (2026-07-14)
The one organ worth reusing NOW is the explicit INTERNAL WORLD-MODEL (typed
concept graph + role-uses in library.py) — carried over to sharpen ERS from a
shape-checker into a checker that can also test a claim against the reasoner's
own asserted model. See the ers world-model proposal (separate, gate-tier).
