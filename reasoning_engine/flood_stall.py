"""
flood_stall.py — the flood-and-stall loop (DRAFTED design, trial realization).

Realizes DESIGN_STATE_2026-07-13.md's 10-step loop for a TRIAL. Not gated, not
declared. Built so the self-check in task (1) has something concrete to bite.

Loop clock = flood/stall rhythm. The four drives (generator.py) are demoted to
EMITTERS inside step 5 — they are NOT the loop's phases anymore.

LANGUAGE BOUNDARY (honest, per design doc "population vs propagation"):
  - Population (new concept / role-use) = LLM-as-compiler. The engine CANNOT do
    this itself. Every such point is marked `LLM_BOUNDARY` and, in this trial,
    is fed from a scripted answer-oracle so the mechanical loop can run and be
    inspected. The oracle stands in for the LLM; it is NOT a claim that
    population is mechanical.
  - Propagation (consequences along existing typed edges) = mechanical. Real.

Judges (evolvable surface, NOT regress-poison):
  - D2 scope: fixed goal-type -> relationship-set table (starting config).
  - D6 select: fixed goal-modulated priority order (starting config).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum

from library import Library, Role
from question import Question, ExtractionAct, Contract
from checker import check_shape
from counter import TreeCounter
from prop_counter import PropCounter


_qseq = 0
def _next_qid(prefix: str) -> str:
    global _qseq
    _qseq += 1
    return f"{prefix}{_qseq}"


# --------------------------------------------------------------------------- #
# Typed relation edges — the thing FLOOD propagates along. library.py's RoleUse
# records role-in-context but carries no consequence to cascade. We add a thin
# directed relation layer WITHOUT touching library.py's model.
# --------------------------------------------------------------------------- #
class RelType(Enum):
    CATEGORY = "category"        # X is-a Y
    ATTRIBUTE = "attribute"      # X has-attribute Y
    DEPENDENCY = "dependency"    # X depends-on Y
    CAUSATION = "causation"      # X causes Y
    CONSTITUENT = "constituent"  # X part-of Y
    CONTRAST = "contrast"        # X contrasts-with Y
    DIFFERENCE = "difference"    # X differs-from Y


@dataclass(frozen=True)
class Relation:
    src: str
    rel: RelType
    dst: str


@dataclass
class Graph:
    """The relation layer that floods. Sits alongside a Library."""
    edges: list[Relation] = field(default_factory=list)
    # facts already floated in during this run (concept ids known-populated)
    populated: set[str] = field(default_factory=set)

    def add(self, src: str, rel: RelType, dst: str) -> None:
        self.edges.append(Relation(src, rel, dst))

    def out_edges(self, cid: str) -> list[Relation]:
        return [e for e in self.edges if e.src == cid]


# --------------------------------------------------------------------------- #
# GOAL — carries a type (drives D2/D6) and a done-state predicate (step 1b).
# --------------------------------------------------------------------------- #
class GoalType(Enum):
    COMPARE = "compare"
    BUILD = "build"
    DIAGNOSE = "diagnose"
    PLAN = "plan"
    CHARACTERIZE = "characterize"


# D2 starting config: fixed goal-type -> in-scope relationship set.
# UNCONFIRMED goal-type set (design doc flags this) — trial values.
D2_SCOPE: dict[GoalType, set[RelType]] = {
    GoalType.COMPARE:      {RelType.CATEGORY, RelType.CONTRAST, RelType.ATTRIBUTE},
    GoalType.BUILD:        {RelType.CONSTITUENT, RelType.DEPENDENCY, RelType.CATEGORY},
    GoalType.DIAGNOSE:     {RelType.CAUSATION, RelType.DEPENDENCY, RelType.CATEGORY},
    GoalType.PLAN:         {RelType.DEPENDENCY, RelType.CONSTITUENT, RelType.DIFFERENCE},
    GoalType.CHARACTERIZE: {RelType.CATEGORY, RelType.ATTRIBUTE},
}

# D6 starting config: fixed base priority; goal's primary relation bumps to front.
D6_BASE_PRIORITY: list[RelType] = [
    RelType.CATEGORY, RelType.DEPENDENCY, RelType.DIFFERENCE,
    RelType.CAUSATION, RelType.CONSTITUENT, RelType.CONTRAST, RelType.ATTRIBUTE,
]

# The goal-meaningful PRIMARY relation per goal-type. The design doc says "the
# goal-type's primary relationship bumps to front" but never defines primary;
# a set has no order, so the trial's alphabetical guess mis-picked (diagnose
# wanted causation, got category). This makes primary explicit. (self-check fix)
D2_PRIMARY: dict[GoalType, RelType] = {
    GoalType.COMPARE:      RelType.CONTRAST,
    GoalType.BUILD:        RelType.CONSTITUENT,
    GoalType.DIAGNOSE:     RelType.CAUSATION,
    GoalType.PLAN:         RelType.DEPENDENCY,
    GoalType.CHARACTERIZE: RelType.CATEGORY,
}


@dataclass
class Goal:
    gtype: GoalType
    focus: str                       # concept id the goal is about
    done_when: set[RelType]          # done-state: these rels populated on focus
    description: str = ""


# --------------------------------------------------------------------------- #
# A resistance point (step 3 Stall output): an in-scope relationship on a
# front concept that has no populated target yet — needs a question.
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Resistance:
    concept: str
    rel: RelType


# --------------------------------------------------------------------------- #
# The oracle stands in for the LLM at every LLM_BOUNDARY. Scripted for the
# trial. Returns either a populate-fact (concept id + relation to add) or None
# (can't answer -> would decompose to subgoal in the full design).
# --------------------------------------------------------------------------- #
@dataclass
class Oracle:
    # (concept, rel) -> (dst_concept_id, dst_label) to populate
    script: dict[tuple[str, RelType], tuple[str, str]]

    def answer(self, r: Resistance):
        return self.script.get((r.concept, r.rel))


# --------------------------------------------------------------------------- #
# STEP 2 — FLOOD. Mechanical propagation along typed edges. No LLM. Bounded by
# the propagation counter (forces progression, does not bounce).
# --------------------------------------------------------------------------- #
def flood(graph: Graph, front: set[str], pc: PropCounter) -> set[str]:
    pc.reset()
    queue = list(front)
    reached = set(front)
    while queue:
        cid = queue.pop(0)
        for e in graph.out_edges(cid):
            if e.dst in reached:
                continue
            if not pc.tick():          # propagation limit -> force progression
                return reached
            reached.add(e.dst)
            graph.populated.add(e.dst)
            queue.append(e.dst)
    return reached


# --------------------------------------------------------------------------- #
# STEP 3 — STALL. Collect resistance: in-scope rels on front concepts with no
# populated target. This is where the flood "stalls" and needs real generation.
# --------------------------------------------------------------------------- #
def stall(graph: Graph, front: set[str], in_scope: set[RelType]) -> list[Resistance]:
    out: list[Resistance] = []
    for cid in sorted(front):
        have = {e.rel for e in graph.out_edges(cid) if e.dst in graph.populated}
        for rel in sorted(in_scope, key=lambda r: r.value):
            if rel not in have:
                out.append(Resistance(cid, rel))
    return out


# --------------------------------------------------------------------------- #
# STEP 4 — D2 SCOPE (judge). Goal-type -> in-scope relationship set.
# --------------------------------------------------------------------------- #
def d2_scope(goal: Goal) -> set[RelType]:
    return D2_SCOPE[goal.gtype]


# --------------------------------------------------------------------------- #
# STEP 6 — D6 SELECT (judge). Only fires if >1 resistance live. Goal-modulated
# priority: the goal-type's primary in-scope rel bumps to front.
# --------------------------------------------------------------------------- #
def d6_select(goal: Goal, live: list[Resistance]) -> Resistance:
    if len(live) == 1:
        return live[0]
    primary = D2_PRIMARY[goal.gtype]          # explicit, not alphabetical
    order = list(D6_BASE_PRIORITY)
    if primary in order:
        order.remove(primary)
        order.insert(0, primary)
    rank = {rel: i for i, rel in enumerate(order)}
    # focus-proximity: resistances ON the goal-focus concept come first. The
    # drafted D6 lacked this, so budget drained into incidental flooded
    # concepts before the goal's own concept. (self-check fix)
    return min(
        live,
        key=lambda r: (0 if r.concept == goal.focus else 1,
                       rank.get(r.rel, 99), r.concept),
    )


# --------------------------------------------------------------------------- #
# STEP 5 — EMIT + GATE. Drives (now emitters) turn resistance into candidate
# questions; shape-check filters. Minimal here: one vector per resistance,
# aimed at the role matching the rel.
# --------------------------------------------------------------------------- #
_REL_TO_ROLE = {
    RelType.CATEGORY: Role.CATEGORY, RelType.ATTRIBUTE: Role.ATTRIBUTE,
    RelType.DEPENDENCY: Role.RELATIONSHIP, RelType.CAUSATION: Role.RELATIONSHIP,
    RelType.CONSTITUENT: Role.RELATIONSHIP, RelType.CONTRAST: Role.RELATIONSHIP,
    RelType.DIFFERENCE: Role.ATTRIBUTE,
}


def emit(r: Resistance, lib: Library, intent: str) -> Question:
    role = _REL_TO_ROLE[r.rel]
    label = lib.concepts[r.concept].label if lib.has_concept(r.concept) else r.concept
    return Question(
        qid=_next_qid("emit_"),
        content_target=role,
        extraction_act=ExtractionAct.GAP_IMPLYING,
        intent_link=intent,
        contract=Contract.C5_BINDING,
        template=f"What {r.rel.value} does {label} have? (in-scope, unpopulated)",
    )


# --------------------------------------------------------------------------- #
# THE LOOP.
# --------------------------------------------------------------------------- #
def run_loop(lib: Library, graph: Graph, goal: Goal, oracle: Oracle,
             tree: TreeCounter, pc: PropCounter, intent: str,
             live_intents: set[str], max_iters: int = 20) -> None:

    front = {goal.focus}
    graph.populated.add(goal.focus)
    in_scope = d2_scope(goal)
    exhausted: set[Resistance] = set()   # resistances a subgoal could not fill

    print(f"GOAL: {goal.gtype.value} on '{goal.focus}' | done_when rels populated: "
          f"{sorted(r.value for r in goal.done_when)}")
    print(f"D2 in-scope rels: {sorted(r.value for r in in_scope)}")
    print(f"tree ceiling={tree.ceiling}  prop limit={pc.limit}\n")

    for it in range(1, max_iters + 1):
        # --- done-state check (step 1b predicate) ---
        have = {e.rel for cid in front for e in graph.out_edges(cid)
                if e.dst in graph.populated}
        if goal.done_when.issubset(have):
            print(f"[iter {it}] DONE-STATE met: {sorted(r.value for r in goal.done_when)} "
                  f"all populated on front.")
            return

        # --- step 2 FLOOD ---
        reached = flood(graph, front, pc)
        forced = pc.forced
        front = reached

        # --- step 3 STALL (minus exhausted resistances) ---
        live = [r for r in stall(graph, front, in_scope) if r not in exhausted]
        print(f"[iter {it}] flood reached {len(reached)} concepts"
              f"{' (prop-limit FORCED progression)' if forced else ''}; "
              f"{len(live)} live resistance points")

        # --- STUCK-STATE predicate (NOT in the drafted design — added by the
        # self-check as a required guard; see critique) ---
        if not live:
            print(f"[iter {it}] STUCK: no live resistance but done-state unmet. "
                  f"The drafted design has no stuck-predicate; without this guard "
                  f"the loop relies on the tree-counter to eventually bounce.")
            return

        # --- step 6 SELECT (D6) ---
        chosen = d6_select(goal, live)
        print(f"           D6 selected: {chosen.concept}.{chosen.rel.value}")

        # --- step 5 EMIT + GATE ---
        q = emit(chosen, lib, intent)
        res = check_shape(q, lib, live_intents)
        if not res.passed:
            print(f"           emit gated OUT: {res.summary} -> exhausted")
            exhausted.add(chosen)
            continue

        # --- step 7 RESOLVE (LLM_BOUNDARY) ---
        adm = tree.admit()
        if not adm.accepted:
            print(f"           TREE ceiling -> BOUNCE TO HUMAN ({adm.count}/{adm.ceiling})")
            return
        ans = oracle.answer(chosen)          # LLM_BOUNDARY: population
        if ans is None:
            print(f"           LLM_BOUNDARY: no direct answer -> subgoal debited "
                  f"(tree {adm.count}/{adm.ceiling}); trial does not recurse -> exhausted")
            exhausted.add(chosen)
            continue

        # --- step 8 INTEGRATE ---
        dst_id, dst_label = ans
        if not lib.has_concept(dst_id):
            lib.add_concept(dst_id, dst_label)
        graph.add(chosen.concept, chosen.rel, dst_id)
        graph.populated.add(dst_id)
        print(f"           INTEGRATE: {chosen.concept} --{chosen.rel.value}--> "
              f"{dst_id} (tree {adm.count}/{adm.ceiling})")

    print(f"\n[max_iters {max_iters} hit] stopping trial.")
