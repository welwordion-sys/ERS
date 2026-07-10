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

## Prepare, then run — the task IS the file

Do not remember to use the ERS mid-task. Instead, the first action on any
gate-tier task is:

    s = ReasonSetter.prepare(goal, "task_name.json", note="...")

This writes the file to disk immediately, stage=prepared, before any
reasoning happens. The task now exists as a checkable artifact independent
of whether anyone finishes it. Continue in the SAME session with normal
ground/propose/check/commit, saving to the same path — stage advances to
in_progress, then committed.

A later session (or an end-of-session audit) calls:

    ReasonSetter.audit_incomplete(["task_name.json", ...])

which lists every file NOT at stage=committed. "Forgot to use the ERS"
becomes impossible to hide: either the file was never prepared (visible
gap in the disposition table) or it was prepared and abandoned (visible
in the audit). This does not by itself stop reasoning-in-prose-then-
backfilling within one sitting — only a genuinely separate blind reader
(see starters, below) catches that. Prepare/run fixes forgetting; it does
not fix backfilling.

## Handoff: ERS starters (a stronger, costlier tool — for blind validation,
not routine use)

Instead of telling a session to use the ERS, give it a starter file whose
task IS the ERS: `export_starter(path)` on the initiating side writes
goal + given/derived facts only — no candidates, no assumptions. The
receiving session loads it with `ReasonSetter.from_starter(path)` and its
job is narrowly propose -> check -> commit. There is nothing to forget:
the task has no other shape. Guards refuse export if a candidate or an
assumed claim would leak through — those are the receiving session's to
generate, or the whole point is defeated.

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
