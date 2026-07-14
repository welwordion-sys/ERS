"""
counter.py — the per-tree containment circuit-breaker + recursion terminator.

architecture.containment_v2: "One hard PER-TREE node counter (total nodes under
root, recursion-INCLUSIVE) is both containment circuit-breaker and recursion
terminator. Below ceiling the decision layer ranks/selects autonomously. At
ceiling the machine ADMITS the size: surfaces the option-space as a fact-list,
bounces the choice to the human."

In this primitive slice the counter guards question ADMISSION into a tree. The
recursive full-engine subgoal call (which also debits this counter) is not built
yet — but the counter is built first, because that call has nowhere to debit
until it exists.

Key design point from spec: at ceiling the counter does NOT silently drop the
candidate. It refuses AND signals bounce_to_human, admitting the tree is
project-sized.
"""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Admission:
    accepted: bool
    at_ceiling: bool          # ceiling reached -> bounce to human
    count: int
    ceiling: int
    note: str = ""


@dataclass
class TreeCounter:
    """Counts nodes admitted under one root goal-tree, recursion-inclusive."""
    ceiling: int
    count: int = 0
    _bounced: bool = field(default=False)

    def admit(self) -> Admission:
        """Attempt to admit one node into the tree. Recursion-inclusive: a
        recursive subgoal call debits here too (same method)."""
        if self.count >= self.ceiling:
            self._bounced = True
            return Admission(
                accepted=False,
                at_ceiling=True,
                count=self.count,
                ceiling=self.ceiling,
                note="tree at ceiling: whole project — surface options as a "
                     "fact-list, give me a task",
            )
        self.count += 1
        return Admission(
            accepted=True,
            at_ceiling=False,
            count=self.count,
            ceiling=self.ceiling,
        )

    @property
    def bounced(self) -> bool:
        return self._bounced
