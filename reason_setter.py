"""ERS setter substrate v0.7 prototype.

Gatekeeper, not diary: state is mutated only through setter calls.

v0.7 (2026-09-26) closes self-report bypasses found by test_befunde.py, design gated in
work_files/2026-09-26_setter_v07/decision_setter_v07.json:
  - checks bind to the target's statement AT CHECK TIME; a check against an earlier
    version of a claim does not count for the current one (and does not block it)
  - I4 requires a SURVIVED falsifier against the answer's current version and refuses
    while an unretracted FAILED one stands against it; retract_check(id, reason) is the
    only way past a flawed falsifier, and every retraction is listed in the commit block
  - check ids are append-only; kind/outcome are a closed vocabulary ("satisfied" is an
    alias of "survived")
  - ground() refuses caller-supplied negation_handling (only check()/carry() set it)
  - changing the statement of an existing id requires `revises` quoting it verbatim (I8)
  - I3 promotion and I9 relevance count only survived, unretracted, current checks
  - import_prior_commit()/reuse() bring the parent closure along, so derived claims import
  - registry ids are unique per commit; legacy duplicate ids are refused as ambiguous
    unless latest=True; reuse() honours registry_path
  - every file is read and written as UTF-8

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
  I3 no silent promotion        — assumed->given only via a SURVIVED check event
  I4 refutation attempted       — commit requires >=1 survived falsifier against the answer's
                                  current version and no unretracted failed one (v0.7)
  I5 assumption duality         — every assumed in commit closure: checked | branched | carried
                                  (carried is always legal, but must be declared; label reflects it);
                                  only check()/carry() may set the handling (v0.7)
  I6 commit-last ordering       — enforced by call sequence; state is frozen after commit
  I7 side-finding disposition   — a check result naming a defect must dispose it
                                  (fixed|filed|carried); added v0.4 from licensed failure LF1
  I8 revision provenance        — recharacterizing a prior claim requires quoting its prior
                                  text verbatim (revises field); added v0.5 from LF5; applies to
                                  re-grounding an existing id with a new statement (v0.7)
  I9 goal relevance              — commit requires a survived relevance check tying the answer's
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
import uuid
from dataclasses import dataclass, field


# ---------------------------------------------------------------- data

VALID_STATUS = ("given", "assumed", "derived")
VALID_KINDS = ("falsifier", "negation", "obligation", "relevance")
VALID_OUTCOMES = ("survived", "failed", "branch_traced")
OUTCOME_ALIASES = {"satisfied": "survived"}
DEFAULT_REGISTRY = "claims_registry.json"


def _tokens(text):
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _load_registry(registry_path):
    try:
        with open(registry_path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _append_registry(registry_path, entries):
    reg = _load_registry(registry_path)
    reg.extend(entries)
    with open(registry_path, "w", encoding="utf-8") as f:
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
    kind: str                       # falsifier | negation | obligation | relevance
    target: str                     # claim or candidate id
    method: str
    result: str                     # non-empty = actually performed
    outcome: str                    # survived | failed | branch_traced
    side_findings: list = None      # I7: [{"finding": str, "disposition": fixed|filed|carried}]
    target_statement: str = None    # v0.7: target's statement at check time (None = legacy file)
    retracted: str = None           # v0.7: reason, set only by retract_check()

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

    def _statement_of(self, tid):
        if tid in self.claims:
            return self.claims[tid].statement
        if tid in self.candidates:
            return self.candidates[tid].statement
        return None

    def _current(self, k):
        """Does check k refer to its target's CURRENT version? Legacy checks (no recorded
        statement) are taken as current, so old files keep their meaning."""
        return k.target_statement is None or k.target_statement == self._statement_of(k.target)

    def _live(self, k):
        """Performed, not retracted, about the current version of its target."""
        return bool(k.result) and not k.retracted and self._current(k)

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
            live = [k for k in self.checks.values()
                    if k.kind == "falsifier" and k.target == cand.id and self._live(k)]
            if any(k.outcome == "failed" for k in live):
                q.append((1, f"candidate {cand.id} refuted by "
                             f"{[k.id for k in live if k.outcome == 'failed']} (current version)"))
            elif not live:
                q.append((2, f"no checked falsifier against candidate {cand.id}"))
        for c in self.claims.values():
            for a in (c.antecedents or []):
                ac = self.claims.get(a)
                if ac is None or (ac.status != "given" and not self._checked(a)):
                    q.append((3, f"antecedent {a} of {c.id} not established"))
        for oid, stmt in self.obligations.items():
            for cand in self.candidates.values():
                if not any(k.kind == "obligation" and k.target == cand.id and oid in k.method
                           and self._live(k) for k in self.checks.values()):
                    q.append((4, f"obligation {oid} ({stmt!r}) unchecked against {cand.id}"))
        q.sort(key=lambda t: t[0])
        return [s for _, s in q]

    def _checked(self, claim_id):
        """A survived, unretracted check against the claim's current version (I3)."""
        return any(k.target == claim_id and k.outcome == "survived" and self._live(k)
                   for k in self.checks.values())

    def _ledger(self):
        return {
            "goals": self.goals,
            "given":   [c.id for c in self.claims.values() if c.status == "given"],
            "assumed": {c.id: (c.negation_handling or "OPEN") for c in self.claims.values()
                        if c.status == "assumed"},
            "derived": [c.id for c in self.claims.values() if c.status == "derived"],
            "candidates": list(self.candidates),
            "obligations": list(self.obligations),
            "retracted_checks": {k.id: k.retracted for k in self.checks.values() if k.retracted},
            "committed": self.committed,
        }

    def _cb(self, ok, phase, reason="", repair="", warnings=None):
        return Callback(ok, phase, reason, repair, warnings or [],
                        self._ledger(), self._queue())

    # -------- phases

    def ground(self, claims):
        """claims: list of dicts (id, statement, status, derived_from?, antecedents?, revises?).
        negation_handling is NOT accepted here — check() and carry() set it (I5)."""
        return self._ground(claims, trusted=False)

    def _ground(self, claims, trusted):
        fr = self._frozen("ground")
        if fr: return fr
        staged = []
        for d in claims:
            if not trusted and d.get("negation_handling") is not None:
                return self._cb(False, "ground",
                    reason=f"{d['id']}: negation_handling is set by check()/carry(), "
                           f"not asserted in ground() (I5)",
                    repair="drop the field; record a negation check() or call carry(id, note)")
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
            old = self.claims.get(c.id)
            if old is not None and old.statement != c.statement:
                # I8 on the same id: a new statement is a recharacterization
                rv = c.revises or {}
                if rv.get("target") != c.id or rv.get("prior_text") != old.statement:
                    return self._cb(False, "ground",
                        reason=f"{c.id}: statement changed without revises quoting it (I8)",
                        repair=f"add revises={{'target': {c.id!r}, 'prior_text': <current statement "
                               f"verbatim>, 'why': ...}}, or ground the new claim under a new id")
            if old is not None and old.status != c.status:
                # I3: assumed -> given only via a survived check event
                if old.status == "assumed" and c.status == "given" and not self._checked(c.id):
                    return self._cb(False, "ground",
                        reason=f"{c.id}: silent promotion assumed->given (I3)",
                        repair=f"record a check event against {c.id} that SURVIVED, or keep it assumed")
            if old is not None and old.statement == c.statement and not trusted:
                # same version re-grounded: handling earned by checks/carry is kept
                c.negation_handling = old.negation_handling
                c.negation_note = old.negation_note
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
                if tgt in self.claims and tgt != c.id and \
                        c.revises.get("prior_text") != self.claims[tgt].statement:
                    return self._cb(False, "ground",
                        reason=f"{c.id}: revises {tgt} but prior_text is not its statement verbatim (I8)",
                        repair=f"quote {tgt}'s statement exactly")
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
        """events: list of dicts (id, kind, target, method, result, outcome, side_findings?).
        kind=falsifier|negation|obligation|relevance; outcome=survived|failed|branch_traced.
        The batch is validated as a whole before anything is recorded. Check ids are
        append-only; withdraw a flawed check with retract_check(). A negation check/branch
        on an assumed claim updates its negation_handling."""
        fr = self._frozen("check")
        if fr: return fr
        known = self._known_ids()
        seen = set()
        staged = []
        for d in events:
            cid = d.get("id")
            if cid in self.checks or cid in seen:
                return self._cb(False, "check",
                    reason=f"check id {cid!r} already recorded — check ids are append-only",
                    repair="use a new id; to withdraw a flawed check call retract_check(id, reason)")
            seen.add(cid)
            if d.get("target") not in known:
                return self._cb(False, "check",
                    reason=f"check {cid} targets unknown id {d.get('target')} (I1)",
                    repair="target an existing claim or candidate")
            if d.get("kind") not in VALID_KINDS:
                return self._cb(False, "check",
                    reason=f"check {cid}: unknown kind {d.get('kind')!r}",
                    repair=f"use one of {VALID_KINDS}")
            if not d.get("result"):
                return self._cb(False, "check",
                    reason=f"check {cid} has empty result — not actually performed",
                    repair="perform the check and record what happened, or drop the event")
            outcome = OUTCOME_ALIASES.get(d.get("outcome"), d.get("outcome"))
            if outcome not in VALID_OUTCOMES:
                res = str(d.get("result", "")).strip().lower()
                swapped = res in ("pass", "fail", "open", "passed", "failed")
                return self._cb(False, "check",
                    reason=f"check {cid}: outcome {str(d.get('outcome'))[:60]!r} is not one of "
                           f"{VALID_OUTCOMES}" + (" — result and outcome look swapped" if swapped else ""),
                    repair="result = what happened (prose); outcome = survived | failed | branch_traced"
                           + ("; a check still open is not performed yet — record it once it ran"
                              if res == "open" else ""))
            staged.append({**d, "outcome": outcome})
        _warn = []
        for d in staged:
            ev = CheckEvent(**{k: d.get(k) for k in ("id", "kind", "target", "method", "result",
                                                      "outcome", "side_findings")},
                            target_statement=self._statement_of(d["target"]))
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
        self._log.append(("check", [d["id"] for d in staged]))
        return self._cb(True, "check", warnings=_warn)

    def retract_check(self, check_id, reason):
        """Withdraw a check that was itself flawed (wrong build measured, wrong target, ...).
        The event stays in the file, marked retracted with the reason; it no longer counts
        for or against anything, and commit() lists every retraction. Retracting is legal,
        hiding the retraction is not — same shape as carry()."""
        fr = self._frozen("retract_check")
        if fr: return fr
        k = self.checks.get(check_id)
        if k is None:
            return self._cb(False, "retract_check", reason=f"unknown check {check_id} (I1)",
                            repair="retract an existing check id")
        if not (reason or "").strip():
            return self._cb(False, "retract_check",
                reason=f"retracting {check_id} without a reason hides the failure",
                repair="say what was wrong with the check itself")
        if k.retracted:
            return self._cb(False, "retract_check", reason=f"{check_id} already retracted",
                            repair="nothing to do")
        k.retracted = reason
        if k.kind == "negation" and k.target in self.claims:
            cl = self.claims[k.target]
            if cl.status == "assumed" and cl.negation_handling in ("checked", "branched"):
                rest = [x for x in self.checks.values() if x.kind == "negation"
                        and x.target == cl.id and self._live(x)]
                cl.negation_handling = (None if not rest else
                                        "checked" if rest[-1].outcome == "survived" else "branched")
                cl.negation_note = rest[-1].result if rest else f"[negation check {check_id} retracted]"
        self._log.append(("retract_check", check_id))
        return self._cb(True, "retract_check")

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
               registry_path=None):
        """The gate. Refuses unless I1-I5, I7, I9 hold for the answer's closure.
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
        if not any(k.kind == "relevance" and k.target in ({answer_claim_id} | closure)
                   and k.outcome == "survived" and self._live(k)
                   for k in self.checks.values()):
            return self._cb(False, "commit",
                reason="no relevance check connecting the answer's evidence to the stated goal(s) (I9)",
                repair=f"run check(kind='relevance', target={answer_claim_id!r}, "
                       f"result='<how the cited evidence bears on: {list(self.goals.values())}>')")

        # I4 — a survived falsifier against the answer's current version (or the candidate it
        # realizes), and no unretracted failed one against it
        targets = {answer_claim_id} | {c.id for c in self.candidates.values()
                                       if c.statement == cl.statement}
        live_f = [k for k in self.checks.values()
                  if k.kind == "falsifier" and k.target in targets and self._live(k)]
        refuted = [k.id for k in live_f if k.outcome == "failed"]
        if refuted:
            return self._cb(False, "commit",
                reason=f"falsifier(s) {refuted} failed against the answer's current version (I4)",
                repair="revise the answer (revises quoting it) and check the new version; if the "
                       "falsifier refuted an EARLIER version or another claim, it should target that; "
                       "if the falsifier itself was flawed, retract_check(id, reason)")
        if not any(k.outcome == "survived" for k in live_f):
            return self._cb(False, "commit",
                reason="no checked falsifier against the answer (I4)",
                repair=f"run check() with kind=falsifier, target={answer_claim_id}, "
                       "non-empty result, outcome=survived")

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
            "retracted_checks": {k.id: k.retracted for k in self.checks.values() if k.retracted},
        }
        self._log.append(("commit", answer_claim_id))
        batch = uuid.uuid4().hex[:8]
        src = getattr(self, "_path", "<unsaved>")
        _append_registry(registry_path or getattr(self, "_registry_path", DEFAULT_REGISTRY), [
            {"reg_id": f"{src}::{cid}::{batch}",
             "claim_id": cid,
             "statement": self.claims[cid].statement,
             "status": self.claims[cid].status,
             "negation_handling": self.claims[cid].negation_handling,
             "derived_from": self.claims[cid].derived_from,
             "source_path": src,
             "commit_batch": batch,
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
        correctness of the judgment is not). The registry path is remembered
        for commit() and reuse()."""
        s = cls(goal_statements)
        s._prep_note = note
        s._registry_path = registry_path
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
            "setter_version": "v0.7",
            "goals": self.goals,
            "prep_note": getattr(self, "_prep_note", ""),
            "registry_path": getattr(self, "_registry_path", DEFAULT_REGISTRY),
            "prior_candidates": getattr(self, "_prior_candidates", []),
            "claims": {k: v.__dict__ for k, v in self.claims.items()},
            "candidates": {k: v.__dict__ for k, v in self.candidates.items()},
            "checks": {k: v.__dict__ for k, v in self.checks.items()},
            "obligations": self.obligations,
            "committed": self.committed,
            "call_log": self._log,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(blob, f, indent=2, ensure_ascii=False)
        return stage

    @classmethod
    def resume(cls, path):
        """RUN continues from a prepared/in_progress file. Loads goal +
        whatever state exists; caller proceeds with propose/check/commit.
        Files written by older versions load unchanged (no vocabulary check on load)."""
        with open(path, encoding="utf-8") as f:
            blob = json.load(f)
        s = cls(list(blob["goals"].values()))
        s._path = path
        s.goals = blob["goals"]
        s._prep_note = blob.get("prep_note", "")
        s._registry_path = blob.get("registry_path", DEFAULT_REGISTRY)
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

    # -------- honest import (LF6)

    def _import_closure(self, src_claims, root_id, prefix, provenance, root_local=None):
        """Ground root_id and its whole parent closure from src_claims (claim_id -> dict),
        preserving each claim's true status and negation handling. Parents are grounded
        first; a claim already imported under the same local id and text is reused.
        Returns the local id of the root."""
        order, seen = [], set()

        def visit(cid, path=()):
            if cid in seen:
                return
            if cid in path:
                raise ValueError(f"derivation cycle at {cid} in {provenance}")
            src = src_claims.get(cid)
            if src is None:
                raise ValueError(f"{cid} not found in {provenance} — cannot import its "
                                 f"derivation honestly")
            for d in (src.get("derived_from") or []):
                for p in d.get("parents", []):
                    visit(p, path + (cid,))
            seen.add(cid)
            order.append(cid)

        visit(root_id)
        local = {cid: (root_local if cid == root_id and root_local else f"{prefix}{cid}")
                 for cid in order}
        batch = []
        for cid in order:
            src = src_claims[cid]
            lid = local[cid]
            if lid in self.claims:
                if self.claims[lid].statement != src["statement"]:
                    raise ValueError(f"local id {lid} already holds a different statement")
                continue
            note = src.get("negation_note", "") or ""
            if src["status"] == "assumed":
                note = (note + f" [imported from {provenance}]").strip()
            batch.append({
                "id": lid,
                "statement": src["statement"],
                "status": src["status"],   # honest: given/assumed/derived as it actually was
                "derived_from": [{"parents": [local[p] for p in d.get("parents", [])],
                                  "rule": d.get("rule", "") + f" (imported from {provenance})"}
                                 for d in (src.get("derived_from") or [])] or None,
                "negation_handling": src.get("negation_handling"),
                "negation_note": note,
            })
        if batch:
            cb = self._ground(batch, trusted=True)
            if not cb.ok:
                raise ValueError(f"import failed: {cb.reason}")
        return local[root_id]

    def reuse(self, reg_id, local_id=None, registry_path=None, latest=False):
        """The static-interface counterpart to prepare()'s surfacing: pull one
        entry from the shared claims registry in verbatim — by the reg_id
        shown in prepare()'s prior_candidates (or any reg_id in the registry
        file, e.g. from a broader manual look) — preserving its true status
        and negation_handling exactly like import_prior_commit does for a
        single named file, and bringing its parent closure along (v0.7).
        Nothing about matching/selection is automatic here: the session picks
        the reg_id. Registries written before v0.7 can hold one reg_id several
        times (every commit to the same path reused it); such an id is refused
        as ambiguous unless latest=True picks the most recent entry.
        Returns the new local claim id."""
        reg = _load_registry(registry_path or getattr(self, "_registry_path", DEFAULT_REGISTRY))
        hits = [i for i, e in enumerate(reg) if e.get("reg_id") == reg_id]
        if not hits:
            raise ValueError(f"{reg_id} not found in registry")
        if len(hits) > 1 and not latest:
            raise ValueError(f"{reg_id} is ambiguous: {len(hits)} registry entries share it "
                             f"(registry written before v0.7); pass latest=True for the most "
                             f"recent, or pick the entry by statement")
        i = hits[-1]
        entry = reg[i]
        batch = entry.get("commit_batch")
        if batch:
            pool = [e for e in reg if e.get("commit_batch") == batch]
        else:
            # legacy registry: one commit's closure was appended as a contiguous run with
            # the same source_path; collect that run around the entry
            pool, names = [], set()
            for rng in (range(i, -1, -1), range(i + 1, len(reg))):
                for j in rng:
                    e = reg[j]
                    if e.get("source_path") != entry["source_path"] or e["claim_id"] in names:
                        break
                    pool.append(e)
                    names.add(e["claim_id"])
        src_claims = {e["claim_id"]: e for e in pool}
        return self._import_closure(src_claims, entry["claim_id"], "reused_",
                                    f"{entry['source_path']}::{entry['claim_id']}",
                                    root_local=local_id)

    def import_prior_commit(self, source_path, claim_id):
        """LF6 fix: import a claim from a DIFFERENT (already committed) file
        honestly — preserving its actual evidence status and negation
        handling, instead of re-grounding it as a fresh 'given' (which
        silently promotes assumed/derived claims and evades I3 across the
        file boundary). Brings the claim's parent closure along (v0.7), so a
        derived claim imports with its derivation. Returns the new local claim
        id (prefixed to avoid collision) so it can be used as a revises() target."""
        with open(source_path, encoding="utf-8") as f:
            src = json.load(f)
        claims = src.get("claims", {})
        if claim_id not in claims:
            raise ValueError(f"{claim_id} not found in {source_path}")
        com = src.get("committed") or {}
        was_in_commit = com.get("answer") == claim_id
        carried = claim_id in com.get("assumptions_carried", [])
        src_claims = {k: dict(v) for k, v in claims.items()}
        if claims[claim_id]["status"] == "assumed":
            src_claims[claim_id]["negation_note"] = (
                (claims[claim_id].get("negation_note", "") or "") +
                f" [was in committed answer: {was_in_commit}, carried: {carried}]")
        return self._import_closure(src_claims, claim_id, "imported_", source_path)

    @staticmethod
    def audit_incomplete(paths):
        """Session-end/audit helper: which ERS files never reached commit."""
        incomplete = []
        for p in paths:
            try:
                with open(p, encoding="utf-8") as f:
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
                "string, v0.7+). Load these given_facts "
                "via ground(), then "
                "propose() your own candidates — do not accept a pre-formed "
                "answer from elsewhere as a candidate without discriminating "
                "it against at least one alternative. check(), then commit()."
            ),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(blob, f, indent=2, ensure_ascii=False)

    @classmethod
    def from_starter(cls, path):
        """Receiving side: load a starter, goal + facts only, ready for propose()."""
        with open(path, encoding="utf-8") as f:
            blob = json.load(f)
        if blob.get("kind") != "ers_starter":
            raise ValueError("not an ers_starter file")
        s = cls(list(blob["goals"].values()))
        s.goals = blob["goals"]
        facts = [{k: v for k, v in f.items() if k != "negation_handling" or v is not None}
                 for f in blob["given_facts"].values()]
        cb = s.ground(facts)
        if not cb.ok:
            raise ValueError(f"starter facts failed to ground: {cb.reason}")
        s.obligations.update(blob.get("obligations", {}))
        return s, blob.get("instructions", "")
