# Worked example: checking perspective/subtraction_design

The originating instance of the protocol (session 2026-07-06). Source
artifact: KB node `perspective/subtraction_design`, specifically the
`VALIDATED_MECHANISM_2026_07_05` 4-phase design and its frontier table.

Files:
- `claims_subtraction.json` — the claims table. Run
  `python3 ../checker.py claims_subtraction.json` (expect: clean).
- `subtraction_check.py` — independent re-implementation of the 4-phase
  mechanism from the node text alone; C1 sweep, node-table consistency,
  C3 reachability sweep. Run it; expect `failures = 0` and
  `(1,0) present: False`.
- `subtraction_table_derivation.py` — derives the frontier table FROM
  ground truth by per-key intersection of valid outputs (does not trust
  the node's table). Expect all keys forced to the node's entries,
  except (1,1,1) where borrow_out is a don't-care.

## What the pattern demonstrates

1. Re-implementation from artifact text = executable cold-read test.
2. Deriving an asserted table from ground truth instead of confirming
   it — the difference between finding errors and inheriting them.
3. Evidence escalation: the reachability claim went sweep -> proof;
   the trigger claim (C4) deliberately stayed at sweep because the
   proof was not actually written. Evidence class records honesty,
   not ambition.

## The C3 proof (closed-form, upgrades the node's open item 4)

Claim: b1=1 (standing borrow after phase 1) implies b2=1 (standing
borrow after phase 2), so frontier keys (1,1,0) and (0,1,0) never
arise, at any width.

1. Phase 2 computes 0 − bit − rb over the phase-1 low result bits,
   LSB→MSB, rb starting 0. While bits are 0 and rb=0: 0−0−0=0, no
   borrow. At the first 1-bit: 0−1−0=−1 → borrow. Once rb=1:
   0−bit−1 ≤ −1 for bit ∈ {0,1}, so the borrow holds to the end.
   Hence b2=0 iff ALL phase-1 low result bits are 0.
2. b1=1 means phase 1 borrowed somewhere. At the FIRST borrow-
   generating position, borrow_in=0, so a_i − b_i < 0 forces
   (a_i,b_i) = (0,1), giving diff −1 → result bit 1. Phase-1 result
   bits are written once and never revisited, so that 1 survives.
3. Therefore b1=1 ⇒ a nonzero low result bit exists ⇒ (by 1) b2=1. ∎

Consequence for rule authoring: the 6-key frontier table is complete
by necessity, not by luck of the sweep. A defensive fallback for the
two missing keys is still cheap insurance against a MALFORMED state
(the proof assumes well-formed phase-1 output), but is not needed for
any well-formed input.
