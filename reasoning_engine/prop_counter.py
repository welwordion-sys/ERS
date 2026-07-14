"""
prop_counter.py — the PROPAGATION counter (new this design, Sven's call).

Distinct from the TREE counter (counter.py):
  - TREE counter bounds the question/subgoal tree, recursion-inclusive; at
    ceiling it BOUNCES TO HUMAN. It contains reasoning SIZE.
  - PROPAGATION counter bounds ONE flood phase; at limit it FORCES PROGRESSION
    to the next loop phase. It does NOT bounce, it ADVANCES. It contains flood
    breadth runaway.

Judgeless (inv_judgeless): a hard count that fires progression, no evaluation.
Resets at the start of each flood phase — it bounds a single flood, not the run.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class PropCounter:
    limit: int
    count: int = 0

    def reset(self) -> None:
        """Called at the start of each Flood phase."""
        self.count = 0

    def tick(self) -> bool:
        """Register one propagation fill. Returns True if the flood may
        CONTINUE, False if the limit forces progression to the next phase.
        Hard read, no judgment."""
        if self.count >= self.limit:
            return False
        self.count += 1
        return True

    @property
    def forced(self) -> bool:
        return self.count >= self.limit
