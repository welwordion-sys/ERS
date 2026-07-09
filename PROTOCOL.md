# ERS Setter Substrate v0.5 — Session Protocol

Gatekeeper, not diary. State is mutated ONLY through setter calls; the setter
refuses invalid moves and freezes after commit. Reason freely BETWEEN calls —
each call is a phase checkpoint, not a per-thought tax.

## Loop

1. `s = ReasonSetter(goal_or_goals)` — one or more goals, both legal.
2. `s.ground(claims)` — everything you rely on, tagged given/assumed/derived.
   Derived claims must cite parents + rule.
3. `s.oblige({...})` — conditions ANY accepted answer must satisfy (optional).
4. `s.propose(candidates)` — one is fine; several want discriminators (advisory).
5. Reason. Then `s.check(events)` — falsifier / negation / obligation events.
   Empty `result` = not performed = refused.
6. For any assumption you will NOT explore: `s.carry(id, note)` — always legal,
   must be declared, note says what might flip.
7. `s.commit(answer_id, evidence_label, assumptions_carried)`
   — refused unless: falsifier checked against the answer, every assumption in
   the closure handled (checked/branched/carried), declared closure exact.
8. `s.save(path)` — the file includes the call log; write order is evidence.

## The callback

Every call returns: ok, reason+repair on refusal, warnings (advisory layer),
the ledger (given/assumed+handling/derived/candidates/committed), and the
ranked inquiry queue:

  polarity-flipping unexplored negations
  > unchecked falsifiers on live candidates
  > unestablished antecedents
  > unchecked obligations

Read the queue after every call. It is the "what should I look at next" — the
compass half of the substrate.

## Hard invariants (cannot be circumvented)

I1 referenced ids exist. I2 derived cites parents+rule. I3 assumed→given only
via a check event. I4 commit needs a checked falsifier against the answer.
I5 every assumed in commit closure is checked/branched/carried — skipping a
negation is legal, hiding the skip is not. I6 commit is last; state freezes.
I7 a check result naming a defect (in anything, including artifacts outside
the work file) must declare it as a side_finding and dispose it: fixed |
filed | carried. Silently absorbing a named defect into SURVIVED is never
legitimate. (v0.4, from licensed failure LF1.)

I8 recharacterizing a prior claim requires a revises field quoting its
prior text verbatim — enforces that the prior commitment was actually
read, not that the new characterization is correct. (v0.5, from LF5.)

I9 commit requires a relevance check tying the answers cited evidence
to the stated goal(s) — enforces that the connection was declared, not
that it holds. Internal coherence alone does not satisfy this. (v0.5, from LF3.)

Advisory: claims using because/therefore/explains-why get a nudge to test
the explanation against a case where the property should differ (LF4) —
not a hard gate; discrimination is semantic and cant be verified mechanically.

## Advisory (warnings, never refusals)

Discriminators when >1 candidate; conditional-looking statements without
antecedents; obligation coverage. Override consciously, not silently.

## Known limit — I9 gameability

I9 requires a relevance check EXIST connecting the answer to the goal; it
cannot verify the connection is real. A fabricated relevance claim
("directly relevant to goal X") passes I9 exactly like a genuine one —
worse than I8, whose quoted prior_text is at least glance-checkable by a
reader. Self-audited 2026-07-08 (workfile_ers_selfaudit_v0_5.json).

## Known limit — do not overclaim

The setter guarantees required support existed BEFORE commitment was possible.
It cannot guarantee the support was causally load-bearing: a solver can reason
silently and perform the phases as theater. Call-order evidence narrows this;
it does not eliminate it.
