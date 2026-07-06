# Reasoning Protocol v0.1

Purpose: a procedure for an LLM session to check reasoning rigorously by
externalizing state into files and delegating mechanical steps to code.
The LLM encodes, selects rules, and judges. Code applies rules, sweeps
cases, and scans for consistency. Verdicts reached by prose alone are
not verdicts.

Origin: distilled 2026-07-06 from a working session (Perspective
subtraction-design check) and the ERS design documents v0.1/v0.4
(drafted with ChatGPT). This protocol is the minimal practical core;
the design documents are the roadmap for extensions.

## The procedure

1. EXTRACT. Read the source artifact (KB node, design doc, code
   comment). List every checkable claim in a claims table conforming to
   `claims_schema.json`. Each claim gets: id, statement, status
   (given / derived / assumed / hypothesis), and — for any claim
   asserting a test or verification result — its reproducer, or the
   literal string UNREPRODUCED.

2. RE-IMPLEMENT FROM TEXT. Build the checking artifact using ONLY the
   source artifact's own text, never memory of the conversation that
   produced it. This doubles as a cold-read test: if the artifact
   cannot be rebuilt from its own text, the artifact has a hole —
   report the hole before patching it from memory.

3. CHECK MECHANICALLY. Run code, not prose:
   - sweeps over input spaces (wider than the original claim's sweep
     where cheap),
   - brute-force derivation of asserted tables/case-analyses from
     ground truth, intersecting valid outputs per key (distinguishes
     forced entries from don't-cares),
   - `checker.py` over the claims table (referential integrity,
     provenance completeness, hypothesis-dependency closure,
     contradiction scan, reproducer presence).

4. ESCALATE EVIDENCE. empirical sweep -> forced-by-intersection ->
   closed-form proof. Upgrade a claim's evidence class only when the
   stronger form is actually in hand. Record which class each verdict
   has. A proof found cheaply (e.g. an invariant argument over a
   sweep) is worth writing down; do not stop at "sweep passed" without
   asking whether the proof is one paragraph away.

5. REPORT WITH MECHANISM. A verdict names WHAT was run (files, exact
   sweep ranges, what was brute-forced) and its evidence class. State
   explicitly which artifacts are committed vs session-scratch; scratch
   = UNREPRODUCED regardless of what it showed.

## Hard rules

- A verdict is valid only if a runnable artifact produced it.
  (Executable corollary of the KB's verification_needs_reproducer.)
- Derived claims carry derived_from (parent ids + rule). Claims
  depending on hypotheses carry hypothesis_deps; consequences of a
  hypothesis never silently become unconditional facts.
- The encoding step is the residual trust point. For each encoded
  claim, ask: what reading of the original statement would make this
  row wrong? Record nontrivial encoding choices in the claim's notes.
- Overhead discipline: this protocol pays off at the depth where
  in-context state-tracking starts failing (multi-step derivations,
  case analyses, asserted tables). For shallow questions, skip it.

## Contradiction resolution policy

The checker DETECTS live contradictions (both sides accepted on the
same hypothesis footing). Resolution is a policy, applied in order:

1. LOCATE. Run `--explain` on both sides; the fault lies in the
   premises, never in the derivation rows. Do not resolve by deleting
   a derived claim — if its parents stand, it will simply be
   re-derived.
2. RETRACT BY EVIDENCE CLASS. Among the premises of the two chains,
   prefer retracting the one with the lowest evidence class
   (none < empirical_sweep < forced_by_intersection < proof).
   Run `--retract` on the candidate FIRST to see the blast radius
   before committing to it.
3. FORK IF TIED. If the weakest premises on both sides have equal
   evidence class, do not choose: convert both into a dual-hypothesis
   pair (P5), move each chain's dependence into hypothesis_deps, and
   let the contradiction become a branch-separated warning. The
   decision is then owed to evidence, not to taste — record what
   observation would discriminate.
4. ENCODING SUSPECT LAST. If both premises hold strong evidence,
   suspect the encoding step (a contradiction between two
   well-verified claims usually means one row misreads its source).
   Re-read both statements against the source artifact's text.

## Known failure modes for a fresh session (read before starting)

- NARRATING THE PROTOCOL: writing a claims table, then "verifying" in
  prose. The table without the code run is theater. Counter: hard rule
  1 — no runnable artifact, no verdict.
- CHECKING FROM MEMORY: re-implementing from the conversation instead
  of the artifact text, which silently patches the artifact's holes
  and defeats the cold-read. Counter: step 2 as written.
- TRUSTING THE ASSERTED TABLE: verifying that code REPRODUCES a
  claimed table instead of DERIVING the table from ground truth. The
  first inherits the table's errors; the second finds them.
- DECORATIVE NUMBERS: attaching probabilities/weights with no
  machinery computing them. Reliability is structural here (status,
  provenance, hypothesis_deps, evidence class), not numeric.
- SCOPE INFLATION: building the full ERS ontology (contexts, goals,
  controller) before the minimal core has earned it. The design docs
  are the roadmap, not the task.

## Files

- `claims_schema.json` — claim row format (P1 atomic facts, P2
  provenance, P3 conditional knowledge from ERS design v0.1; nothing
  else).
- `checker.py` — mechanical checks over a claims file. Run:
  `python3 checker.py <claims.json>`; exit 0 = clean. Also:
  `--retract ID` (simulate withdrawing a premise: transitive
  lost-support report, read-only) and `--explain ID` (derivation
  tree with status, evidence class, reproducers).
- `worked_example/` — the originating instance: claims table for
  Perspective's subtraction_design node, the two checking harnesses,
  and the closed-form unreachability proof. Learn the pattern from
  this before reading anything else.
