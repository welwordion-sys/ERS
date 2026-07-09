# ERS — Epistemic Reasoning Substrate

Two instances live in this repo. **The setter (v0.4) is current.**

## Current: setter substrate v0.4

- `reason_setter.py` — state mutated only through setter calls; seven hard
  invariants enforced at write time (I7 side-finding disposition added in
  v0.4 from licensed failure LF1); ranked inquiry queue in every callback.
- `test_setter.py` — smoke tests (replays the cycle-3 false-commit shape).
- `PROTOCOL.md` — **the protocol to follow.** Read this one.

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
`PROTOCOL.md`. The checker remains only as the predecessor the worked
example depends on; it validates files the setter makes unnecessary.

Key difference: the checker inspects a finished file (diary — can be
backfilled); the setter refuses invalid moves at write time and freezes
after commit (gatekeeper — write order is in the artifact).
