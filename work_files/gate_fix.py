from reason_setter import ReasonSetter

s, stage = ReasonSetter.resume("world_model_format_gate.json")
print("resumed at stage:", stage)

s.check([
  {"id":"chk_relevance_b","kind":"relevance","target":"ans_b",
   "method":"Tie ans_b's evidence directly to the stated goal's half (b): how transitivity is licensed so ground truth cannot be contaminated by unsound derivation.",
   "result":"The goal's (b) half asks how propagation is licensed such that ground truth is not contaminated. ans_b's evidence bears directly: f_nondistribution establishes that blanket transitivity IS the contamination mechanism (car is-red -> wheel is-red); f_exceptions_unbounded establishes that patching it with exceptions cannot be made safe; f_ers_format supplies the inversion (declare-to-travel) that makes undeclared channels inert rather than exceptional. The answer therefore discharges (b) directly, with its residual limit (a wrongly-declared channel still contaminates) named in chk_falsify_b rather than hidden.",
   "outcome":"satisfied","side_findings":None},
])

r = s.commit("ans_b","derived",assumptions_carried=[])
print("COMMIT ans_b ok:", r.ok, "|", r.reason)
if r.ok:
    print("committed:", r.ledger["committed"]["statement"][:90], "...")
print("stage:", s.save("world_model_format_gate.json"))
print("residual queue:", r.queue)
