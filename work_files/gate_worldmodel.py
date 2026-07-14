from reason_setter import ReasonSetter

GOAL = ("Decide whether the reasoning_engine internal world-model (typed concept "
        "graph + role-uses) should be transplanted into ERS as a semantic-"
        "consistency check layer, given ERS currently checks reasoning SHAPE only.")

s = ReasonSetter.prepare([GOAL], "worldmodel_transplant_gate.json",
    note=("Archived flood-and-stall engine had no correctness oracle; ERS shape-"
          "check cannot catch a well-formed but false claim. Literature: grounding "
          "at the population boundary is the paradigm's unsolved failure mode."))

# --- GROUND: given facts (from the trial + the three searches) ---
s.ground([
  {"id":"f_ers_shape","statement":"ERS today checks reasoning SHAPE (grounded, has-falsifier, no-orphan) and does not model what the reasoner asserts to be true about the world.","status":"given"},
  {"id":"f_shape_gap","statement":"A claim can be shape-valid and semantically false simultaneously; shape-checking cannot distinguish them.","status":"given"},
  {"id":"f_wm_exists","statement":"reasoning_engine already contains a typed world-model: concepts, role-uses on edges, and typed relations, sufficient to test whether a referent exists and whether an asserted relation contradicts a populated one.","status":"given"},
  {"id":"f_grounding_unsolved","statement":"Independent literature reports grounding failure (referents not matching context, hallucinated propositions) as the dominant failure mode even when the LLM is confined to pure translation.","status":"given"},
])

# --- OBLIGE: what any accepted answer must satisfy ---
s.oblige({
  "o_adds_power":"must let ERS catch at least one error class it provably cannot catch now",
  "o_no_oracle_overclaim":"must not claim to verify TRUTH against the world — only consistency against the reasoner's own asserted model",
  "o_bounded":"must not require ERS to itself populate the world-model via LLM (that reintroduces the unsolved grounding problem inside the checker)",
})

# --- derived answer ---
s.ground([
  {"id":"ans","status":"derived",
   "statement":"Transplant the world-model as a CONSISTENCY layer beside ERS: a claim is checked for whether its referents exist in the asserted model and whether it contradicts an already-populated relation. It checks consistency-against-asserted-model, NOT truth-against-world. Population of the model stays the human/reasoner's job, not ERS's.",
   "derived_from":[{"parents":["f_ers_shape","f_shape_gap","f_wm_exists"],
     "rule":"shape-check has a known gap (f_shape_gap); the world-model can test the missing dimension (f_wm_exists); add it as a distinct consistency layer without claiming it closes the truth gap"}]},
])

s.propose([{"id":"cand_ans","statement":"Add world-model as an ERS consistency-check layer (not a truth oracle).","discriminator":"vs. leaving ERS shape-only, or vs. claiming full semantic verification"}])

# --- CHECKS: falsifier, obligation, relevance ---
s.check([
  {"id":"chk_falsify","kind":"falsifier","target":"ans",
   "method":"Find a case where the consistency layer gives false assurance — passes a claim that is still false.",
   "result":"A claim can be fully consistent with the asserted model AND false, if the model itself is wrong (garbage-in). So the layer does NOT catch truth errors; it only catches claims inconsistent with what was asserted. This is a real limit, not a defect of the proposal — it is exactly why o_no_oracle_overclaim exists. The proposal survives ONLY in its narrowed form (consistency, not truth); the broad form (verifies correctness) is falsified.",
   "outcome":"survived","side_findings":[{"finding":"broad 'verifies truth' reading is false; only the narrow consistency claim holds","disposition":"fixed"}]},
  {"id":"chk_oblige","kind":"obligation","target":"ans",
   "method":"Does it satisfy o_adds_power / o_no_oracle_overclaim / o_bounded?",
   "result":"o_adds_power: yes — catches referent-nonexistence and relation-contradiction, neither reachable by shape-check. o_no_oracle_overclaim: satisfied by construction (consistency-only). o_bounded: satisfied — ERS reads an already-populated model, it does not populate it.",
   "outcome":"satisfied","side_findings":None},
  {"id":"chk_relevance","kind":"relevance","target":"ans",
   "method":"Tie the answer to the goal.",
   "result":"Goal asked whether to transplant the world-model into ERS. Answer says yes but only as a consistency layer with an explicit scope boundary — directly discharging the decision with its own limit named.",
   "outcome":"satisfied","side_findings":None},
])

r = s.commit("ans","derived",assumptions_carried=[])
print("COMMIT:", r)
print("stage on disk:", s.save("worldmodel_transplant_gate.json"))
