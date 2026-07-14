"""
fs_trial.py — trial run of the flood-and-stall loop with the STARTING CONFIGS.

Goal: compare 'bob' — done when {category, contrast, attribute} are populated on
the front (matches D2 COMPARE scope).

Seeds a small graph with SOME edges present (so flood has something to cascade)
and SOME gaps (so stall produces real resistance the oracle then fills).
"""

from __future__ import annotations
from library import Library, Role
from counter import TreeCounter
from prop_counter import PropCounter
from flood_stall import (
    Graph, RelType, Goal, GoalType, Oracle, run_loop,
)


def build() -> tuple[Library, Graph, Goal, Oracle]:
    lib = Library()
    for cid, label in [
        ("bob", "Bob"), ("alice", "Alice"), ("mammal", "mammal"),
        ("height", "height"), ("warm_blooded", "warm-blooded"),
        ("reptile", "reptile"),
    ]:
        lib.add_concept(cid, label)
    # role-uses so the shape-checker's used_in_role() resolves the targets emit
    # aims at (Category/Attribute/Relationship all need material).
    lib.use("bob", Role.ENTITY, "bob")
    lib.use("mammal", Role.CATEGORY, "bob")
    lib.use("height", Role.ATTRIBUTE, "bob")
    lib.use("reptile", Role.RELATIONSHIP, "bob")   # gives Relationship material

    graph = Graph()
    # present edges -> flood cascades bob -> mammal -> warm_blooded
    graph.add("bob", RelType.CATEGORY, "mammal")
    graph.add("mammal", RelType.ATTRIBUTE, "warm_blooded")
    graph.populated.update({"bob", "mammal", "warm_blooded"})
    # NOTE: bob has category (populated) but NOT contrast or attribute-of-bob.
    # Those are the in-scope gaps stall will surface for the COMPARE goal.

    goal = Goal(
        gtype=GoalType.COMPARE,
        focus="bob",
        done_when={RelType.CATEGORY, RelType.CONTRAST, RelType.ATTRIBUTE},
        description="compare Bob against kin",
    )

    # Oracle scripts the LLM population answers for the resistances stall raises.
    oracle = Oracle(script={
        ("bob", RelType.CONTRAST): ("reptile", "reptile"),
        ("bob", RelType.ATTRIBUTE): ("height", "height"),
    })
    return lib, graph, goal, oracle


def main() -> None:
    lib, graph, goal, oracle = build()
    tree = TreeCounter(ceiling=6)
    pc = PropCounter(limit=10)
    intent = "i_compare"
    run_loop(lib, graph, goal, oracle, tree, pc, intent,
             live_intents={intent})
    print(f"\nfinal: tree {tree.count}/{tree.ceiling} bounced={tree.bounced}; "
          f"graph edges={len(graph.edges)}")


if __name__ == "__main__":
    main()
