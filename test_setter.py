"""Smoke tests: does the setter refuse what checker v0.1 let through?

Case A replays the cycle-3 failure shape: correct arithmetic, a load-bearing
claim asserted but never checked, commit attempted anyway.
Case B is the honest path through the same problem.
"""
from reason_setter import ReasonSetter


def case_a_false_commit():
    s = ReasonSetter("compute 5 - 3 as single-token result under match-order M")
    s.ground([
        {"id": "c1", "statement": "operands are 5 and 3", "status": "given"},
        {"id": "c2", "statement": "match order M is legal", "status": "given"},
        {"id": "c3", "statement": "result is single token", "status": "assumed"},  # the false claim
        {"id": "c4", "statement": "5-3=2 with single-token sign-correct result",
         "status": "derived",
         "derived_from": [{"parents": ["c1", "c2", "c3"], "rule": "spine subtraction"}]},
    ])
    # solver tries to commit WITHOUT ever checking c3 (this is what cycle 3 did)
    cb = s.commit("c4", "assumed", ["c3"])
    assert not cb.ok, "setter must refuse: no falsifier on answer"
    print("A1 refused (no falsifier):", cb.reason)

    # solver adds a falsifier on the answer but still never handles c3's negation
    cb = s.check([{"id": "k1", "kind": "falsifier", "target": "c4",
                   "method": "recompute value", "result": "value 2 correct",
                   "outcome": "survived"}])
    assert cb.ok
    cb = s.commit("c4", "assumed", ["c3"])
    assert not cb.ok, "setter must refuse: c3 negation unhandled"
    print("A2 refused (I5):", cb.reason)
    print("A2 queue head:", cb.queue[0])
    return s


def case_b_honest_path():
    s = ReasonSetter("compute 5 - 3 as single-token result under match-order M")
    s.ground([
        {"id": "c1", "statement": "operands are 5 and 3", "status": "given"},
        {"id": "c2", "statement": "match order M is legal", "status": "given"},
        {"id": "c3", "statement": "result is single token", "status": "assumed"},
        {"id": "c4", "statement": "5-3=2 single-token sign-correct",
         "status": "derived",
         "derived_from": [{"parents": ["c1", "c2", "c3"], "rule": "spine subtraction"}]},
    ])
    # negation of c3 actually traced -> branch shows it FAILS under order M'
    cb = s.check([
        {"id": "k1", "kind": "negation", "target": "c3",
         "method": "enumerate legal match orders",
         "result": "under order M' result is two tokens, sign token dropped — polarity flips",
         "outcome": "branch_traced"},
        {"id": "k2", "kind": "falsifier", "target": "c4",
         "method": "recompute under both orders",
         "result": "holds under M only", "outcome": "survived"},
        {"id": "k3", "kind": "relevance", "target": "c4",
         "method": "connect evidence to goal",
         "result": "goal asks for single-token result under order M; c4 states exactly that "
                   "value and token-count under M, directly answering the goal (not a side fact)",
         "outcome": "survived"},
    ])
    assert cb.ok
    cb = s.commit("c4", "assumed", ["c3"])
    assert cb.ok, cb.reason
    print("B committed:", s.committed)

    # I6: nothing moves after commit
    cb = s.ground([{"id": "c9", "statement": "backfill", "status": "given"}])
    assert not cb.ok
    print("B post-commit write refused (I6):", cb.reason)
    return s


def case_c_silent_promotion():
    s = ReasonSetter("toy")
    s.ground([{"id": "a1", "statement": "X holds", "status": "assumed"}])
    cb = s.ground([{"id": "a1", "statement": "X holds", "status": "given"}])
    assert not cb.ok, "silent promotion must be refused"
    print("C refused (I3):", cb.reason)


if __name__ == "__main__":
    case_a_false_commit()
    print()
    case_b_honest_path()
    print()
    case_c_silent_promotion()
    print("\nall smoke tests passed")
