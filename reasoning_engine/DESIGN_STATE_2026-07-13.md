# reasoning_engine — Design state, end of 2026-07-13

STATUS: **ADVANCED BUT NOT DECLARED.** The starting design is NOT frozen.
Sven ended the session at reduced discernment and explicitly deferred
declaration. Do NOT treat anything below as gated/settled. First task next
session: ratify or revise this, fresh, THEN declare/gate. A wrong handover has
cost a session before — do not repeat by mistaking momentum for decision.

## The loop — "flood-and-stall" formulation (drafted, Claude-synthesized, NOT
## yet confirmed by Sven against his original four-drive sketch)

1. Instantiate — stated givens populated into library (LLM-compiled).
2. Flood — mechanical propagation along existing typed edges runs; consequences
   autofill/cascade, no LLM, until no no-resistance fill remains OR the
   propagation counter forces progression (see counters).
3. Stall — collect live resistance points (questions needing population or real
   generation, not answerable by propagation).
4. Scope (D2 judge) — goal-bound: which relationships are in-scope for concepts
   at the front. Starting config = fixed table (below).
5. Emit + gate — drives emit candidate questions for in-scope-empty
   relationships; precondition-gating + shape-check filter (mechanical).
6. Select (D6 judge) — only fires if >1 resistance point live; goal-bound: which
   to pursue. Starting config = fixed priority order (below).
7. Resolve — selected question -> LLM: answer directly (populate) or decompose
   into subgoal (recursive engine call, debits TREE counter).
8. Integrate — answer's facts written to library.
9. Contingency — fires only on tree-counter threshold (gated invariant).
10. Loop back to Flood. Terminate on done-state met OR tree-counter ceiling
    bounce-to-human.

KEY CLAIM (needs Sven's confirmation): the loop's clock is the flood/stall
rhythm; the four drives (know/do/reveal/contingency) are EMITTERS inside step 5,
NOT the loop's phases. This differs from Sven's original sketch where the drives
WERE the cycle. THIS IS THE #1 THING TO CONFIRM before declaring.

## Goal binding — THREE sites (drafted)

The goal must STEER, not just bookend. It binds at:
- D2 (goal -> in-scope relationships)
- D6 (goal -> which question pursued next)
- Done-state establishment (early, concrete success-predicate; goal has no finish
  line without it — currently step ~1b, was missing from earlier loop drafts)
Between these sites the machine runs goal-blind and mechanical (correct).
Weak-goal-binding was the diagnosed flaw; three-site binding is the drafted fix.

## Counters — TWO distinct, distinct jobs (Sven confirmed the second this session)

- TREE counter (exists, counter.py): bounds question/subgoal tree,
  recursion-inclusive; at ceiling -> BOUNCE TO HUMAN. Contains reasoning SIZE.
- PROPAGATION counter (NEW, Sven's call): a hard count that bounds one flood
  phase; at limit -> FORCE PROGRESSION to next loop phase (does NOT bounce,
  ADVANCES). Prevents exploration/flood runaway on breadth. Judgeless (a count
  that fires progression).
Correctly noted this session: the tree counter does NOT stop propagation. That
was a real hole; the propagation counter fills it.

## D2 starting config (fixed goal-type -> relationship-set table; judgeless v0,
## evolved by feedback). Goal-type list PARTLY INFERRED from seed stock — Sven
## has NOT confirmed the goal-type set.
- compare/differentiate -> {category, contrast, attribute}
- build/construct       -> {constituent, dependency, category}
- diagnose/explain      -> {causation, dependency, category}
- plan/achieve          -> {dependency, constituent, difference}  (MEA/HTN tier-0)
- characterize/identify -> {category, attribute, relation-general}
Rule: match goal-type, pull that set into scope, rest out-of-scope.

## D6 starting config (fixed goal-modulated priority order; judgeless v0)
Default priority: identity/category -> dependency -> difference -> causation ->
constituent. Goal-modulation: the goal-type's primary relationship (from D2)
bumps to front. Fire highest-ranked live question. Learning surface = the order
+ bump size; later replaced by fixed-weight probabilistic variant (creativity
experiment).

## Population vs propagation boundary (settled this session, honest)
- Population (new concept / role-use assignment) = LLM-as-compiler, exclusively,
  for now. It is FREQUENT. ERS CANNOT populate — it only checks. Any design
  assuming frequent language-free population is assuming away the hard part.
- Propagation (consequences along existing typed edges) = mechanical, LLM-free,
  floods freely.
- FUTURE (not now): a primitive compiler for hard-pattern-matchable "obvious"
  population cases, conservative-with-LLM-fallback, output gated by ERS. Raises
  mechanical:LLM ratio. "Obvious" must mean hard-pattern-match, NEVER "seems
  easy." Do not build pre-emptively.

## Identity (settled this session)
Identity is NOT completion (complete identity = whole relationship network in a
complete world-model = unreachable). Procedurally, identity = "what scope of
relationships do we need to START with" = a bootstrapping question, terminating
when starting-scope is filled, NOT when concept is exhausted. This is why D2
(scope) exists and why the identity drive terminates by design.

## Judges are the evolvable surface (settled this session)
D2 and D6 are NOT regress-poison to be eliminated. They are explicit, isolated,
feedback-evolved judges — the primary place testing feedback is needed.
inv_judgeless forbids HIDDEN judges inside firing conditions, not named evolvable
ones. Drives fire mechanically; scope + selection are the two judges.

## Conditional future component (banked, do NOT build pre-emptively)
Observe concept-space growth rate under flood-and-stall. IF the front over-grows
(hits ceiling on breadth of goal-irrelevant reachable structure before reaching
goal), add a perception/perspective filter constraining what the flood surfaces
-- as a HARD-READ salience gate (perspective declares in-scope types) or
evolvable judge, NEVER inline relevance assessment. Possibly folds together with
the propagation-counter as the flood's shape-brake. Trigger = observation, not
assumption.

## Still owed before declaration
- Sven confirms the loop formulation (#1 above) vs his original sketch.
- Sven confirms/corrects the goal-type set (D2 table spine).
- Then: declare starting design, gate the structural commitments.
- THEN build the flat generator (per HANDOVER.md build job).

## Prior gated invariants (STILL HOLD, committed loop_invariants_gate.json)
inv_judgeless (drives fire on hard reads; no judged firing condition) and
inv_no_knob (variants studied between clean runs, not runtime params; weights
fixed/mechanical). These constrain everything above.
