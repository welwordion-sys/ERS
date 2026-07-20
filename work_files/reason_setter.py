"""ERS setter substrate v0.6 prototype.

Gatekeeper, not diary: state is mutated only through setter calls.

v0.6 reuse registry (LF6): commit() auto-appends its answer's claim closure
to a shared claims_registry.json; prepare() (the sole task-start point)
keyword-overlaps the goal against the registry and surfaces prior_candidates
before any reasoning; reuse(reg_id) pulls one in verbatim, preserving its
status/negation_handling. Surfacing is enforced (it lives inside prepare);
sameness judgment is not — same epistemic status as I9. No new hard
invariant, no new check kind.

Hard invariants (truth conditions, uncircumventable):
  I1 referential integrity      — referenced ids exist
  I2 stated dependencies        — derived claims cite parents+rule
  I3 no silent promotion        — assumed->given only via an explicit check event
  I4 refutation attempted       — commit requires >=1 checked falsifier against the answer
  I5 assumption duality         — every assumed in commit closure: checked | branched | carried
                                  (carried is always legal, but must be declared; label reflects it)
  I6 commit-last ordering       — enforced by call sequence; state is frozen after commit
  I7 side-finding disposition   — a check result naming a defect must dispose it
                                  (fixed|filed|carried); added v0.4 from licensed failure LF1
  I8 revision provenance        — recharacterizing a prior claim requires quoting its prior
                                  text verbatim (revises field); added v0.5 from LF5
  I9 goal relevance              — commit requires a relevance check tying the answer's
                                  evidence to goals; enforces existence of the connection,
                                  not its correctness (semantic truth stays unverifiable
                                  mechanically); added v0.5 from LF3
  advisory: explanatory claims ("because"/"explains why") get a nudge to check against
  a discriminating counter-case; LF4 — cannot be a hard gate, discrimination is semantic

Everything else (discriminators, binary-goal duality, conditionals) is ADVISORY:
warnings in the callback, never refusals.

Usage: free-form reasoning happens BETWEEN calls; calls are phase checkpoints.
Every call returns a Callback: accepted/rejected, reason+repair, ledger delta,
ranked inquiry queue. Rejection never loses state — fix and retry.
"""

import json
import re
from dataclasses import dataclass, field


# ---------------------------------------------------------------- data

VALID_STATUS = ("given", "assumed", "derived")
DEFAULT_REGISTRY = "claims_registry.json"


def _tokens(text):
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _load_registry(registry_path):
    try:
        with open(registry_path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _append_registry(registry_path, entries):
    reg = _load_registry(registry_path)
    reg.extend(entries)
    with open(registry_path, "w") as f:
        json.dump(reg, f, indent=2, ensure_ascii=False)

@dataclass
class Claim:
    id: str
    statement: str
    status: str                     # given | assumed | derived
    derived_from: list = None       # [{"parents": [...], "rule": "..."}] for derived
    antecedents: list = None        # for conditionals (advisory)
    negation_handling: str = None   # for assumed: None(open) | checked | branched | carried
    negation_note: str = ""         # what the handling consisted of / what flips
    revises: dict = None            # LF5: {"target": prior_claim_id, "prior_text": quoted, "why": str}

@dataclass
class Candidate:
    id: str
    statement: str
    discriminator: str = ""         # advisory

@dataclass
class CheckEvent:
    id: str
    kind: str                       # falsifier | negation | obligation
    target: str                     # claim or candidate id
    method: str
    result: str                     # non-empty = actually performed
    outcome: str                    # survived | failed | branch_traced
    side_findings: list = None      # I7: [{"finding": str, "disposition": fixed|filed|carried}]

@dataclass
class Callback:
    ok: bool
    phase: str
    reason: str = ""
    repair: str = ""
    warnings: list = field(default_factory=list)
    ledger: dict = field(default_factory=dict)
    queue: list = field(default_factory=list)

    def render(self):
        return json.dumps(self.__dict__, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------- setter

class ReasonSetter:
    def __init__(self, goal_statements):
        """goals: one or more (multi-goal is legal)."""
        if isinstance(goal_statements, str):
            goal_statements = [goal_statements]
        if not goal_statements:
            raise ValueError("at least one goal required")
        self.goals = {f"g{i+1}": s for i, s in enumerate(goal_statements)}
        self.claims = {}      # id -> Claim
        self.candidates = {}  # id -> Candidate
        self.checks = {}      # id -> CheckEvent
        self.obligations = {} # id -> statement (must hold for ANY accepted answer)
        self.committed = None # set once; freezes state (I6)
        self._log = []        # ordered call log (the thing a post-hoc file can't fake)

    # -------- internal helpers

    def _frozen(self, phase):
        if self.committed is not None:
            return Callback(False, phase,
                reason="state frozen: commit already recorded (I6)",
                repair="start a new work file; committed state is immutable")
        return None

    def _known_ids(self):
        return set(self.claims) | set(self.candidates) | set(self.checks) | set(self.goals)

    def _closure(self, cid):
        """Transitive parent closure of a claim id; returns (all_ids, assumed_ids, missing_ids)."""
        seen, assumed, missing, stack = set(), set(), set(), [cid]
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.add(x)
            c = self.claims.get(x)
            if c is None:
                missing.add(x)
                continue
            if c.status == "assumed":
                assumed.add(x)
            for d in (c.derived_from or []):
                stack.extend(d.get("parents", []))
        return seen, assumed, missing

    def _queue(self):
        """Ranked open frontier, computed from state."""
        q = []
        for k in self.checks.values():
            for f in (k.side_findings or []):
                if f.get("disposition") not in ("fixed", "filed", "carried"):
                    q.append((0, f"UNDISPOSED side-finding in {k.id}: {f.get('finding','?')} (I7)"))
        for c in self.claims.values():
            if c.status == "assumed" and c.negation_handling in (None, "carried"):
                flip = "polarity unknown"
                if c.negation_note:
                    flip = c.negation_note
                rank = 0 if "flip" in (c.negation_note or "").lower() else 1
                q.append((rank, f"negation of {c.id} ({c.statement!r}) "
                                f"{'unhandled' if c.negation_handling is None else 'carried, unexplored'}: {flip}"))
        for cand in self.candidates.values():
            if not any(k.kind == "falsifier" and k.target == cand.id and k.result
                       for k in self.checks.values()):
                q.append((2, f"no checked falsifier against candidate {cand.id}"))
        for c in self.claims.values():
            for a in (c.antecedents or []):
                ac = self.claims.get(a)
                if ac is None or (ac.status != "given" and not self._checked(a)):
                    q.append((3, f"antecedent {a} of {c.id} not established"))
        for oid, stmt in self.obligations.items():
            for cand in self.candidates.values():
                if not any(k.kind == "obligation" and k.target == cand.id and oid in k.method
                           for k in self.checks.values()):
                    q.append((4, f"obligation {oid} ({stmt!r}) unchecked against {cand.id}"))
        q.sort(key=lambda t: t[0])
        return [s for _, s in q]

    def _checked(self, claim_id):
        return any(k.target == claim_id and k.result for k in self.checks.values())

    def _ledger(self):
        return {
            "goals": self.goals,
            "given":   [c.id for c in self.claims.values() if c.status == "given"],
            "assumed": {c.id: (c.negation_handling or "OPEN") for c in self.claims.values()
                        if c.status == "assumed"},
            "derived": [c.id for c in self.claims.values() if c.status == "derived"],
            "candidates": list(self.candidates),
            "obligations": list(self.obligations),
            "committed": self.committed,
        }

    def _cb(self, ok, phase, reason="", repair="", warnings=None):
        return Callback(ok, phase, reason, repair, warnings or [],
                        self._ledger(), self._queue())

    # -------- phases

    def ground(self, claims):
        """claims: list of dicts (id, statement, status, derived_from?, antecedents?)."""
        fr = self._frozen("ground")
        if fr: return fr
        staged = []
        for d in claims:
            c = Claim(id=d["id"], statement=d["statement"], status=d["status"],
                      derived_from=d.get("derived_from"),
                      antecedents=d.get("antecedents"),
                      negation_handling=d.get("negation_handling"),
                      negation_note=d.get("negation_note", ""),
                      revises=d.get("revises"))
            if c.status not in VALID_STATUS:
                return self._cb(False, "ground",
                    reason=f"{c.id}: invalid status {c.status!r}",
                    repair=f"use one of {VALID_STATUS}")
            if c.id in self.claims and self.claims[c.id].status != c.status:
                old = self.claims[c.id].status
                # I3: assumed -> given only via a check event
                if old == "assumed" and c.status == "given" and not self._checked(c.id):
                    return self._cb(False, "ground",
                        reason=f"{c.id}: silent promotion assumed->given (I3)",
                        repair=f"record a check event against {c.id} first, or keep it assumed")
            if c.status == "derived":
                if not c.derived_from:
                    return self._cb(False, "ground",
                        reason=f"{c.id}: derived without derived_from (I2)",
                        repair="cite parents and rule, or mark it assumed")
                for d2 in c.derived_from:
                    if not d2.get("parents") or not d2.get("rule"):
                        return self._cb(False, "ground",
                            reason=f"{c.id}: derivation missing parents or rule (I2)",
                            repair="each derivation entry needs parents:[...] and rule:str")
            if c.revises:
                tgt = c.revises.get("target")
                if not c.revises.get("prior_text"):
                    return self._cb(False, "ground",
                        reason=f"{c.id}: revises {tgt} without quoting the prior text (I8)",
                        repair="quote the prior committed statement verbatim before recharacterizing it")
                if tgt not in self._known_ids() and tgt not in {x.id for x in staged}:
                    return self._cb(False, "ground",
                        reason=f"{c.id}: revises unknown id {tgt} (I1)",
                        repair="target an existing claim")
            staged.append(c)
        # I1 across the batch (allow intra-batch references)
        known = self._known_ids() | {c.id for c in staged}
        for c in staged:
            refs = set()
            for d2 in (c.derived_from or []):
                refs |= set(d2.get("parents", []))
            refs |= set(c.antecedents or [])
            unknown = refs - known
            if unknown:
                return self._cb(False, "ground",
                    reason=f"{c.id}: references unknown ids {sorted(unknown)} (I1)",
                    repair="ground those claims first or fix the ids")
        warnings = []
        for c in staged:
            self.claims[c.id] = c
            if c.antecedents is None and re.search(
                    r"\b(if|then|implies)\b|=>", c.statement, re.IGNORECASE):
                warnings.append(f"{c.id} looks conditional but declares no antecedents (advisory)")
            if re.search(r"\b(because|therefore|explains why|accounts for|due to)\b",
                         c.statement, re.IGNORECASE):
                warnings.append(f"{c.id} explains why a property holds/varies — has this been "
                                f"checked against a case where it should differ? (advisory, LF4)")
        self._log.append(("ground", [c.id for c in staged]))
        return self._cb(True, "ground", warnings=warnings)

    def propose(self, candidates):
        fr = self._frozen("propose")
        if fr: return fr
        for d in candidates:
            self.candidates[d["id"]] = Candidate(
                id=d["id"], statement=d["statement"],
                discriminator=d.get("discriminator", ""))
        warnings = []
        if len(self.candidates) > 1:
            for c in self.candidates.values():
                if not c.discriminator:
                    warnings.append(f"{c.id} has no discriminator among "
                                    f"{len(self.candidates)} candidates (advisory)")
        self._log.append(("propose", [d["id"] for d in candidates]))
        return self._cb(True, "propose", warnings=warnings)

    def oblige(self, obligations):
        """obligations: dict id -> statement. Conditions any accepted answer must satisfy."""
        fr = self._frozen("oblige")
        if fr: return fr
        self.obligations.update(obligations)
        self._log.append(("oblige", list(obligations)))
        return self._cb(True, "oblige")

    def check(self, events):
        """events: list of dicts (id, kind, target, method, result, outcome).
        kind=falsifier|negation|obligation. A negation check/branch on an assumed
        claim updates its negation_handling."""
        fr = self._frozen("check")
        if fr: return fr
        known = self._known_ids()
        _warn = []
        for d in events:
            if d["target"] not in known:
                return self._cb(False, "check",
                    reason=f"check {d['id']} targets unknown id {d['target']} (I1)",
                    repair="target an existing claim or candidate")
            if not d.get("result"):
                return self._cb(False, "check",
                    reason=f"check {d['id']} has empty result — not actually performed",
                    repair="perform the check and record what happened, or drop the event")
            ev = CheckEvent(**d)
            self.checks[ev.id] = ev
            if not ev.side_findings and re.search(
                    r"\b(defect|hazard|stale|contradicts|wrong|missing|unimplemented)\b",
                    ev.result, re.IGNORECASE):
                _warn.append(f"{ev.id}: result text names a possible defect but declares no "
                             f"side_findings — declare + dispose, or rephrase (advisory, I7)")
            if ev.kind == "negation" and ev.target in self.claims:
                cl = self.claims[ev.target]
                if cl.status == "assumed":
                    cl.negation_handling = ("checked" if ev.outcome == "survived"
                                            else "branched")
                    cl.negation_note = ev.result
        self._log.append(("check", [d["id"] for d in events]))
        return self._cb(True, "check", warnings=_warn)

    def carry(self, claim_id, note):
        """Explicitly carry an assumption with negation unexplored. Always legal;
        must be declared. note should say what is unknown / what might flip."""
        fr = self._frozen("carry")
        if fr: return fr
        cl = self.claims.get(claim_id)
        if cl is None:
            return self._cb(False, "carry", reason=f"unknown claim {claim_id} (I1)",
                            repair="ground it first")
        if cl.status != "assumed":
            return self._cb(False, "carry",
                reason=f"{claim_id} is {cl.status}, only assumed claims are carried",
                repair="carry applies to assumptions only")
        cl.negation_handling = "carried"
        cl.negation_note = note
        self._log.append(("carry", claim_id))
        return self._cb(True, "carry")

    def commit(self, answer_claim_id, evidence_label, assumptions_carried,
               registry_path=DEFAULT_REGISTRY):
        """The gate. Refuses unless I1-I5 hold for the answer's closure.
        On success state freezes (I6)."""
        fr = self._frozen("commit")
        if fr: return fr
        cl = self.claims.get(answer_claim_id)
        if cl is None:
            return self._cb(False, "commit",
                reason=f"answer {answer_claim_id} is not a grounded claim (I1)",
                repair="ground the answer as a claim first")

        closure, assumed, missing = self._closure(answer_claim_id)
        if missing:
            return self._cb(False, "commit",
                reason=f"closure references missing claims {sorted(missing)} (I1/I2)",
                repair="ground them or fix parent ids")

        # I9 — relevance: cited evidence must be tied to the stated goal(s), not just internally coherent
        if not any(k.kind == "relevance" and k.target in ({answer_claim_id} | closure) and k.result
                   for k in self.checks.values()):
            return self._cb(False, "commit",
                reason="no relevance check connecting the answer's evidence to the stated goal(s) (I9)",
                repair=f"run check(kind='relevance', target={answer_claim_id!r}, "
                       f"result='<how the cited evidence bears on: {list(self.goals.values())}>')")

        # I4 — checked falsifier against the answer (or the candidate it realizes)
        targets = {answer_claim_id} | {c.id for c in self.candidates.values()
                                       if c.statement == cl.statement}
        if not any(k.kind == "falsifier" and k.target in targets and k.result
                   for k in self.checks.values()):
            return self._cb(False, "commit",
                reason="no checked falsifier against the answer (I4)",
                repair=f"run check() with kind=falsifier, target={answer_claim_id}, "
                       "non-empty result")

        # I7 — every declared side-finding disposed
        undisposed = [(k.id, f.get("finding","?")) for k in self.checks.values()
                      for f in (k.side_findings or [])
                      if f.get("disposition") not in ("fixed", "filed", "carried")]
        if undisposed:
            return self._cb(False, "commit",
                reason=f"undisposed side-findings: {undisposed} (I7)",
                repair="give each a disposition: fixed | filed | carried — silently "
                       "absorbing a named defect is never legitimate")

        # I5 — every assumed in closure handled
        unhandled = [a for a in assumed
                     if self.claims[a].negation_handling not in
                        ("checked", "branched", "carried")]
        if unhandled:
            return self._cb(False, "commit",
                reason=f"assumptions with unhandled negation in closure: {sorted(unhandled)} (I5)",
                repair="for each: check() the negation, trace the branch, or carry() it explicitly")

        # honest closure accounting
        declared = set(assumptions_carried)
        actual = assumed
        if declared != actual:
            return self._cb(False, "commit",
                reason=f"assumptions_carried mismatch: declared {sorted(declared)}, "
                       f"actual closure {sorted(actual)}",
                repair="declare exactly the assumed claims in the closure")
        want = "derived" if not actual else "assumed"
        if evidence_label != want:
            return self._cb(False, "commit",
                reason=f"evidence_label {evidence_label!r} but closure says {want!r}",
                repair=f"use evidence_label={want!r}")

        self.committed = {
            "answer": answer_claim_id,
            "statement": cl.statement,
            "evidence_label": evidence_label,
            "assumptions_carried": sorted(actual),
            "carried_unexplored": sorted(a for a in actual
                if self.claims[a].negation_handling == "carried"),
        }
        self._log.append(("commit", answer_claim_id))
        _append_registry(registry_path, [
            {"reg_id": f"{getattr(self, '_path', '<unsaved>')}::{cid}",
             "claim_id": cid,
             "statement": self.claims[cid].statement,
             "status": self.claims[cid].status,
             "negation_handling": self.claims[cid].negation_handling,
             "derived_from": self.claims[cid].derived_from,
             "source_path": getattr(self, "_path", "<unsaved>"),
             "goals": list(self.goals.values())}
            for cid in ({answer_claim_id} | closure)
        ])
        return self._cb(True, "commit")

    # -------- persistence

    @classmethod
    def prepare(cls, goal_statements, path, note="", registry_path=DEFAULT_REGISTRY, top_n=5):
        """PREPARE: write the task to disk before any reasoning happens.
        Stage 'prepared' is a visible, checkable artifact — the task now
        exists independent of whether anyone finishes it. Call this FIRST,
        before ground/propose/check, not after reasoning is done.

        Also the static reuse-interface point: scores every entry in the
        shared claims registry by plain keyword overlap against the goal(s)
        and attaches the top matches as prior_candidates — surfaced, not
        enforced. Nothing is refused; the point is that a session sees what
        may already exist before it types anything fresh. Judging whether a
        surfaced candidate is actually the same fact is left to the session,
        same epistemic status as I9 (existence of the check is enforced,
        correctness of the judgment is not)."""
        s = cls(goal_statements)
        s._prep_note = note
        goal_words = set()
        for g in s.goals.values():
            goal_words |= _tokens(g)
        scored = []
        for entry in _load_registry(registry_path):
            overlap = len(goal_words & _tokens(entry.get("statement", "")))
            if overlap:
                scored.append((overlap, entry))
        scored.sort(key=lambda t: -t[0])
        s._prior_candidates = [e for _, e in scored[:top_n]]
        s.save(path)
        return s

    def save(self, path):
        self._path = path
        stage = "committed" if self.committed else (
            "in_progress" if (self.claims or self.candidates or self.checks)
            else "prepared")
        blob = {
            "stage": stage,
            "goals": self.goals,
            "prep_note": getattr(self, "_prep_note", ""),
            "prior_candidates": getattr(self, "_prior_candidates", []),
            "claims": {k: v.__dict__ for k, v in self.claims.items()},
            "candidates": {k: v.__dict__ for k, v in self.candidates.items()},
            "checks": {k: v.__dict__ for k, v in self.checks.items()},
            "obligations": self.obligations,
            "committed": self.committed,
            "call_log": self._log,
        }
        with open(path, "w") as f:
            json.dump(blob, f, indent=2, ensure_ascii=False)
        return stage

    @classmethod
    def resume(cls, path):
        """RUN continues from a prepared/in_progress file. Loads goal +
        whatever state exists; caller proceeds with propose/check/commit."""
        with open(path) as f:
            blob = json.load(f)
        s = cls(list(blob["goals"].values()))
        s._path = path
        s.goals = blob["goals"]
        s._prep_note = blob.get("prep_note", "")
        s._prior_candidates = blob.get("prior_candidates", [])
        for cid, cd in blob.get("claims", {}).items():
            s.claims[cid] = Claim(**cd)
        for cid, cd in blob.get("candidates", {}).items():
            s.candidates[cid] = Candidate(**cd)
        for kid, kd in blob.get("checks", {}).items():
            s.checks[kid] = CheckEvent(**kd)
        s.obligations.update(blob.get("obligations", {}))
        s.committed = blob.get("committed")
        s._log = blob.get("call_log", [])
        return s, blob.get("stage")

    @classmethod
    def run(cls, path):
        """Named counterpart to prepare() — the 'run' half of prepare/run.
        Alias for resume(): loads a prepared/in_progress file so the caller
        can proceed with ground/propose/check/commit."""
        return cls.resume(path)

    def reuse(self, reg_id, local_id=None):
        """The static-interface counterpart to prepare()'s surfacing: pull one
        entry from the shared claims registry in verbatim — by the reg_id
        shown in prepare()'s prior_candidates (or any reg_id in the registry
        file, e.g. from a broader manual look) — preserving its true status
        and negation_handling exactly like import_prior_commit does for a
        single named file. Generalizes import_prior_commit so a session does
        not need to already know which file a prior claim lives in; it only
        needs the registry, which prepare() already showed it.
        Nothing about matching/selection is automatic here: the session picks
        the reg_id. Returns the new local claim id."""
        entry = next((e for e in _load_registry(DEFAULT_REGISTRY)
                      if e.get("reg_id") == reg_id), None)
        if entry is None:
            raise ValueError(f"{reg_id} not found in registry")
        local_id = local_id or f"reused_{entry['claim_id']}"
        cb = self.ground([{
            "id": local_id,
            "statement": entry["statement"],
            "status": entry["status"],
            "negation_handling": entry.get("negation_handling"),
            "negation_note": f"[reused from {entry['source_path']}::{entry['claim_id']}]",
        }])
        if not cb.ok:
            raise ValueError(f"reuse failed: {cb.reason}")
        return local_id

    def import_prior_commit(self, source_path, claim_id):
        """LF6 fix: import a claim from a DIFFERENT (already committed) file
        honestly — preserving its actual evidence status and negation
        handling, instead of re-grounding it as a fresh 'given' (which
        silently promotes assumed/derived claims and evades I3 across the
        file boundary). Returns the new local claim id (prefixed to avoid
        collision) so it can be used as a revises() target."""
        with open(source_path) as f:
            src = json.load(f)
        src_claim = src.get("claims", {}).get(claim_id)
        if src_claim is None:
            raise ValueError(f"{claim_id} not found in {source_path}")
        local_id = f"imported_{claim_id}"
        was_in_commit = (src.get("committed") or {}).get("answer") == claim_id
        carried = claim_id in (src.get("committed") or {}).get("assumptions_carried", [])
        cb = self.ground([{
            "id": local_id,
            "statement": src_claim["statement"],
            "status": src_claim["status"],   # honest: given/assumed/derived as it actually was
            "derived_from": [{"parents": [f"imported_{p}" for p in d.get("parents", [])],
                              "rule": d.get("rule", "") + " (imported, parents not re-grounded — "
                                      "external provenance)"}
                             for d in (src_claim.get("derived_from") or [])] or None,
            "negation_handling": src_claim.get("negation_handling"),
            "negation_note": src_claim.get("negation_note", "") +
                (f" [imported from {source_path}, was in committed answer: {was_in_commit}, "
                 f"carried: {carried}]" if src_claim["status"] == "assumed" else ""),
        }])
        if not cb.ok:
            raise ValueError(f"import failed: {cb.reason}")
        return local_id

    @staticmethod
    def audit_incomplete(paths):
        """Session-end/audit helper: which ERS files never reached commit."""
        incomplete = []
        for p in paths:
            try:
                with open(p) as f:
                    blob = json.load(f)
                if blob.get("stage") != "committed":
                    incomplete.append((p, blob.get("stage"), blob.get("goals")))
            except (FileNotFoundError, json.JSONDecodeError):
                continue
        return incomplete

    def export_starter(self, path, instructions=""):
        """Handoff artifact for a SEPARATE session: goal + given/derived facts
        ONLY. No candidates, no assumed claims, no partial commit — a receiving
        session must propose and discriminate for itself, so no pre-formed
        answer exists to backfill toward."""
        if self.candidates:
            raise ValueError("starter must not carry candidates — the receiving "
                             "session generates its own or it's just theater with "
                             "extra steps")
        assumed_leak = [c.id for c in self.claims.values() if c.status == "assumed"]
        if assumed_leak:
            raise ValueError(f"starter must not carry assumed claims {assumed_leak} — "
                             "only given facts and their pure derivations belong in a "
                             "starter; assumptions are the receiving session's to make")
        blob = {
            "kind": "ers_starter",
            "goals": self.goals,
            "given_facts": {k: v.__dict__ for k, v in self.claims.items()
                            if v.status in ("given", "derived")},
            "obligations": self.obligations,
            "instructions": instructions or (
                "Your task is to complete this ERS work file, not to reason "
                "freely about the goal. Fetch reason_setter.py + PROTOCOL.md "
                "from https://github.com/welwordion-sys/ERS (verify version "
                "string, v0.6+ for the reuse registry). Load these given_facts "
                "via ground(), then "
                "propose() your own candidates — do not accept a pre-formed "
                "answer from elsewhere as a candidate without discriminating "
                "it against at least one alternative. check(), then commit()."
            ),
        }
        with open(path, "w") as f:
            json.dump(blob, f, indent=2, ensure_ascii=False)

    @classmethod
    def from_starter(cls, path):
        """Receiving side: load a starter, goal + facts only, ready for propose()."""
        with open(path) as f:
            blob = json.load(f)
        if blob.get("kind") != "ers_starter":
            raise ValueError("not an ers_starter file")
        s = cls(list(blob["goals"].values()))
        s.goals = blob["goals"]
        cb = s.ground([{**v} for v in blob["given_facts"].values()])
        if not cb.ok:
            raise ValueError(f"starter facts failed to ground: {cb.reason}")
        s.obligations.update(blob.get("obligations", {}))
        return s, blob.get("instructions", "")
