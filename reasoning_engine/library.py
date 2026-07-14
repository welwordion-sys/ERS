"""
library.py — the reality-builder's store (part 1).

Core model c_A: the four functions (Entity / Category / Relationship / Attribute)
are usage-ROLES, not types. A concept has NO fixed type. Therefore the role
lives on the EDGE (how a concept is used HERE), never on the concept node.

Minimal in-memory graph:
  - Concept:  a node. Just an id + label. No role baked in.
  - RoleUse:  an edge. records that concept `used` is being USED in `role`
              within the context of concept `context` (the four-role write).

This is deliberately thin: enough for a question's content-target to resolve
against something real, no more.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class Role(Enum):
    ENTITY = "Entity"            # used as an instanceable individual
    CATEGORY = "Category"        # used to class other concepts
    RELATIONSHIP = "Relationship"  # used as an operator connecting concepts
    ATTRIBUTE = "Attribute"      # used as structured operand-material


@dataclass(frozen=True)
class Concept:
    cid: str
    label: str


@dataclass(frozen=True)
class RoleUse:
    """A concept `used` deployed in `role`, within `context`.

    e.g. RoleUse(used='height', role=ATTRIBUTE, context='bob') reads as
    'height is used as an Attribute in the context of bob'.
    """
    used: str      # concept id being used
    role: Role
    context: str   # concept id providing the context of use


@dataclass
class Library:
    concepts: dict[str, Concept] = field(default_factory=dict)
    uses: list[RoleUse] = field(default_factory=list)

    def add_concept(self, cid: str, label: str) -> Concept:
        c = Concept(cid, label)
        self.concepts[cid] = c
        return c

    def use(self, used: str, role: Role, context: str) -> RoleUse:
        if used not in self.concepts:
            raise KeyError(f"unknown concept used: {used!r}")
        if context not in self.concepts:
            raise KeyError(f"unknown context concept: {context!r}")
        u = RoleUse(used, role, context)
        self.uses.append(u)
        return u

    def has_concept(self, cid: str) -> bool:
        return cid in self.concepts

    def roles_of(self, cid: str) -> set[Role]:
        """Every role this concept has been USED in anywhere. A concept can
        legitimately carry several — that is c_A in action."""
        return {u.role for u in self.uses if u.used == cid}

    def used_in_role(self, role: Role) -> set[str]:
        """All concept ids ever used in this role. Lets a content-target that
        names a role-slot resolve against real material."""
        return {u.used for u in self.uses if u.role == role}
