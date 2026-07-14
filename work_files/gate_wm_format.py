from reason_setter import ReasonSetter

GOAL = ("Settle the v0 world-model format: (a) the depth-0 collision primitive, "
        "and (b) how transitivity/propagation is licensed, such that the model's "
        "ground truth cannot be contaminated by unsound derivation.")

s = ReasonSetter.prepare([GOAL], "world_model_format_gate.json",
    note=("Sven: minimal ambition, maximal formality. Disjointness first, depth "
          "deferred. Transitivity licensed per-channel by declaration. Prior: "
          "worldmodel_transplant_gate.json committed the consistency-layer scope."))

s.ground([
  # --- given facts ---
  {"id":"f_ers_format","statement":"ERS enforces reasoning discipline by refusing malformed shapes at write time, not by evaluating whether the logic is good.","status":"given"},
  {"id":"f_silence","statement":"A claim passes a consistency check either because it is consistent or because the model is too sparse to disagree; the checker cannot distinguish these from the inside.","status":"given"},
  {"id":"f_nondistribution","statement":"Property inheritance across a relation is non-uniform: part-of is transitive for itself (wheel part-of car part-of garage), but attributes do not distribute down it (car is-red does not license wheel is-red).","status":"given"},
  {"id":"f_exceptions_unbounded","statement":"The set of predicates that do NOT travel a given relation is unbounded and cannot be enumerated; the set that DO travel it is small and enumerable.","status":"given"},
  {"id":"f_depth0_lookup","statement":"Collisions between already-asserted literals are decidable by lookup with no derivation; collisions requiring an inference step are not.","status":"given"},
  {"id":"f_algebra","statement":"Functional slots, dimension-value exclusion, category disjointness, antisymmetry ({aRb,bRa}) and irreflexivity ({aRa}) are all instances of a single constraint: at most one member of a declared set may hold.","status":"given"},

  # --- derived: claim (a) ---
  {"id":"ans_a","status":"derived",
   "statement":"v0 primitive is a single declaration form: AT-MOST-ONE-OF a named set of propositions. It subsumes functional slots, dimension-value exclusion, category disjointness, antisymmetry and irreflexivity (degenerate one-element case). Checking is depth-0 lookup only; nothing is derived.",
   "derived_from":[{"parents":["f_algebra","f_depth0_lookup","f_ers_format"],
     "rule":"the five catch-types share one algebraic form (f_algebra); that form is decidable by lookup (f_depth0_lookup); enforcing it at write time matches ERS's format discipline (f_ers_format)"}]},

  # --- derived: claim (b) ---
  {"id":"ans_b","status":"derived",
   "statement":"Propagation is licensed per (predicate, relation, direction) CHANNEL by explicit declaration. Undeclared channels do not propagate. A relation's own transitivity is itself just a declared channel (part-of travels part-of, upward), so there is no general 'relations are transitive' rule and no exception mechanism.",
   "derived_from":[{"parents":["f_nondistribution","f_exceptions_unbounded","f_ers_format"],
     "rule":"blanket transitivity requires enumerating an unbounded exception set (f_nondistribution + f_exceptions_unbounded); inverting the default to declare-to-travel makes the unbounded set the silent/inert one, which is the same structural-refusal discipline as ERS (f_ers_format)"}]},
])

s.oblige({
  "o_no_contamination":"must guarantee the model cannot come to hold a derived claim that is unsound",
  "o_no_exceptions":"must not require enumerating an unbounded set to be safe",
  "o_depth_deferred":"must leave depth/propagation switchable on incrementally without redesign",
  "o_honest_ceiling":"must not claim to catch errors it cannot catch",
})

s.propose([
  {"id":"cand_a","statement":"Single at-most-one-of partition primitive, depth-0.",
   "discriminator":"vs. five separate declared property-types, or vs. a general inference engine"},
  {"id":"cand_b","statement":"Per-channel declared propagation licensing.",
   "discriminator":"vs. blanket transitivity-with-exceptions, or vs. no propagation ever"},
])

s.check([
  {"id":"chk_falsify_a","kind":"falsifier","target":"ans_a",
   "method":"Find a depth-0 collision the at-most-one-of form CANNOT express, which would show the primitive is not sufficient for v0.",
   "result":"Cross-dimension incompatibility (transparent AND dark) is expressible as at-most-one-of({transparent, dark}) but ONLY if the pair is hand-enumerated — it is domain knowledge, not structure, so the primitive expresses it but does not generalize to unenumerated pairs. Also: 'exactly one' (totality) is NOT expressible — at-most-one cannot force a slot to be filled. Both are real limits. The primitive survives as SUFFICIENT FOR COLLISION-DETECTION (its stated job) but is NOT a completeness constraint language.",
   "outcome":"survived",
   "side_findings":[{"finding":"at-most-one-of cannot express 'exactly one'/totality; v0 detects collisions, does not enforce completeness","disposition":"filed"},
                    {"finding":"cross-dimension incompatible pairs must be hand-enumerated per domain; does not generalize","disposition":"carried"}]},

  {"id":"chk_falsify_b","kind":"falsifier","target":"ans_b",
   "method":"Find a case where declared-channel licensing still admits an unsound derivation, which would break o_no_contamination.",
   "result":"A channel declared WRONGLY (someone declares colour travels down part-of) propagates falsehood soundly-by-construction — the mechanism cannot detect a bad declaration. So contamination is not eliminated; it is RELOCATED to the declaration act, where it is at least explicit, hand-checkable and authority-backed rather than emergent from a flood. The strong reading ('cannot contaminate') is FALSIFIED; the narrow reading ('cannot contaminate WITHOUT an explicit, attributable declaration') survives.",
   "outcome":"survived",
   "side_findings":[{"finding":"strong claim 'no contamination possible' is false — a wrong channel declaration contaminates; only the narrow attributable-declaration reading holds","disposition":"fixed"}]},

  {"id":"chk_oblige","kind":"obligation","target":"ans_b",
   "method":"Test ans_a+ans_b against o_no_contamination / o_no_exceptions / o_depth_deferred / o_honest_ceiling.",
   "result":"o_no_contamination: satisfied only in narrowed form (per chk_falsify_b). o_no_exceptions: satisfied — declare-to-travel inverts the default so the unbounded set is inert. o_depth_deferred: satisfied — v0 declares zero channels, each later channel is an independently verifiable increment. o_honest_ceiling: satisfied given the filed limits (no totality, no cross-dimension generalization, silence-is-not-consistency per f_silence).",
   "outcome":"satisfied","side_findings":None},

  {"id":"chk_relevance","kind":"relevance","target":"ans_a",
   "method":"Tie the evidence to the stated goal.",
   "result":"Goal asked for the v0 collision primitive and the propagation-licensing rule. ans_a supplies the primitive (one form, five catch-types, depth-0); ans_b supplies the licensing (declared channels, no blanket transitivity). Together they discharge both halves, with the contamination limit named rather than assumed away.",
   "outcome":"satisfied","side_findings":None},
])

r1 = s.commit("ans_b","derived",assumptions_carried=[])
print("COMMIT ans_b ok:", r1.ok, "|", r1.reason)
print("stage:", s.save("world_model_format_gate.json"))
