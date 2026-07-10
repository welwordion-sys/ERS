# ERS — Epistemic Reasoning Substrate

Two instances live in this repo. **The setter (v0.5) is current.**

## Current: setter substrate v0.5

- `reason_setter.py` — state mutated only through setter calls; nine hard
  invariants enforced at write time; ranked inquiry queue in every callback.
- `test_setter.py` — smoke tests (replays the cycle-3 false-commit shape).
- `PROTOCOL.md` — **the protocol to follow.** Read this one.

**Default usage — prepare, then run:** the first action on any task is
`ReasonSetter.prepare(goal, "task_name.json")`, which writes the task to
disk before any reasoning happens (stage=prepared). Continue in the same
session with ground/propose/check/commit; stage advances to in_progress,
then committed. `ReasonSetter.audit_incomplete([...])` lists anything not
committed — "forgot to use it" becomes a visible file state, not a silent
omission.

**Starters** (`export_starter`/`from_starter`) are a separate, costlier
mechanism for handoff to a genuinely blind second session — reserved for
validating the setter itself (blind-cycle promotion), not routine use.

Stage: drafted. Not yet validated by a blind cycle. Do not treat as a
standing order until promoted.

## Predecessor: checker v0.2 (kept for the worked example)

- `checker.py` — post-hoc linter over a finished claims file.
- `claims_schema.json` — its schema.
- `reasoning_protocol.md` — its protocol. Superseded by `PROTOCOL.md`;
  do not follow for new work.
- `worked_example/` — subtraction validation case, wired to `checker.py`.
  Historically valuable: the originating run of the protocol.

## Which do I use?

New work: setter. `from reason_setter import ReasonSetter`, follow
`PROTOCOL.md`, start with `prepare()`. The checker remains only as the
predecessor the worked example depends on; it validates files the setter
makes unnecessary.

Key difference: the checker inspects a finished file (diary — can be
backfilled); the setter refuses invalid moves at write time and freezes
after commit (gatekeeper — write order is in the artifact).
